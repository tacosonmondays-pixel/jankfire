--!strict
-- THE OWNER'S DEV MENU, the client half (server/OwnerDev.server.luau checks and does every command; docs/OWNER-DEV.md).
-- two parts:
--   everyone's: a body the server freezes (attribute DevFrozen) is held still here, by its own client (the client owns
--     its body), and let go when the attribute goes
--   the owner's (the place's creator, and only after the server says so): the menu, and the powers the server switched
--     on, read from the owner's own attributes (DevFly = speed, DevNoclip, DevSpeed, DevArms):
--       fly: WASD or the stick where the camera looks, Space / pad A up, Ctrl or C / pad B down, nothing pressed holds
--         you in the air (the movement script stands down while Body.flying: Move.client)
--       noclip: the body's parts stop colliding (the Humanoid still stands on floors), so walls are air
--       run speed: Body.devSpeed, x the run speed (Move.client)
--       weapons in the hub: DevArms (the hub's weapon checks let it through); a weapon picked here goes into the
--         loadout's try layer (never saved), like trying one in training
--       invisible: DevInvisible (the server hides the body): your own client draws a faint ghost of you (DevWas)
--     everyone's too: the red card (DevFx): the owner's arm up with a card, a whistle, a red card on the target's screen;
--     a gift's toast ("GIFT · 5 CRATES")
--     the GIFT tab: give anyone (or you) containers in any number, bundles, items, Brass (the coins), tickets, VIP, Robux weapons;
--       or EVERYONE HERE / ALL SERVERS (19 Nov: the players there right now, once each; ALL SERVERS asks twice)
--     the ANNOUNCE tab: a line for everyone in this server or every server (the server filters it first; the banner is
--       AnnounceBanner.client's, the chat line is giftChat's)
--     the menu: F8, "/dev" in chat, or the small DEV button (touch, pad: VIEW reaches it); with AIM KEYS on (off by
--     default; X is also the grapple's reel-in) X flings, Z freezes or lets go and Y shows a red card to whoever you
--     look at, and a DEV KEYS ON chip shows. it works everywhere, matches too: a match a power touches counts for nothing (the
--     server flags it; the status line says so)
-- plain and functional on purpose: no flavour text (the owner's rule)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local me = Players.LocalPlayer

-- ------------------------------------------------------------------ everyone's: held still while frozen
do
	local held: BasePart? = nil
	local function hold()
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if me:GetAttribute("DevFrozen") == true then
			if root then
				root.AssemblyLinearVelocity = Vector3.zero
				root.Anchored = true
				held = root
			end
		elseif held then
			local r = held :: BasePart
			held = nil
			if r.Parent then
				r.Anchored = false
				r.AssemblyLinearVelocity = Vector3.zero
			end
		end
	end
	me:GetAttributeChangedSignal("DevFrozen"):Connect(hold)
	me.CharacterAdded:Connect(function(ch)
		held = nil
		ch:WaitForChild("HumanoidRootPart", 5)
		hold()
	end)
end

-- ------------------------------------------------------------------ everyone's: the red card (DevFx "redcard")
-- the owner's arm goes up with a red card in the hand for `pose` s (set over the animation every physics step, so it
-- wins), a referee's whistle blows where they stand, and the one it's for sees a red card pop up on their screen
do
	local Fx = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("DevFx", 60) :: RemoteEvent?
	local function cardPart(): Part
		local c = Instance.new("Part")
		c.Name = "DevRedCard"
		c.Size = Vector3.new(0.85, 1.2, 0.06)
		c.Color = Color3.fromRGB(212, 30, 38)
		c.Material = Enum.Material.SmoothPlastic
		c.CanCollide, c.CanQuery, c.CanTouch, c.Massless = false, false, false, true
		c.CastShadow = false
		return c
	end
	local function pose(ch: Model, secs: number)
		local arm = ch:FindFirstChild("RightUpperArm")
		local sh = arm and arm:FindFirstChild("RightShoulder") :: Motor6D?
		local fore = ch:FindFirstChild("RightLowerArm")
		local el = fore and fore:FindFirstChild("RightElbow") :: Motor6D?
		local hand = ch:FindFirstChild("RightHand") :: BasePart?
		if not sh or not hand then return end
		local card = cardPart()
		card.CFrame = hand.CFrame * CFrame.new(0, -0.8, 0)
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = hand, card
		w.Parent = card
		card.Parent = ch
		local t0 = os.clock()
		local conn: RBXScriptConnection
		conn = RunService.Stepped:Connect(function()
			local t = os.clock() - t0
			if t > secs or not sh.Parent then
				conn:Disconnect()
				card:Destroy()
				return
			end
			-- up in 0.15 s, held, down in the last 0.15 s
			local a = math.clamp(math.min(t / 0.15, (secs - t) / 0.15), 0, 1)
			a = a * a * (3 - 2 * a)
			sh.Transform = CFrame.identity:Lerp(CFrame.Angles(math.rad(172), 0, math.rad(-8)), a)
			if el then el.Transform = el.Transform:Lerp(CFrame.identity, a) end
		end)
	end
	local function whistle(id: string, at: BasePart?)
		local s = Instance.new("Sound")
		s.Name = "DevWhistle"
		s.SoundId = id
		s.Volume = 0.8
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = 14
		s.RollOffMaxDistance = 260
		s.Parent = at or workspace
		s:Play()
		task.delay(4, function() s:Destroy() end)
	end
	-- a gift to someone, said in the chat for everyone (the server's line: "<giver> gifted <receiver> <what>"), in the gold
	-- accent: the legacy chat's system message (this place's), or a TextChatService system message if the place moves
	local function giftChat(text: string)
		local line = string.sub(text, 1, 200)
		local TCS = game:GetService("TextChatService")
		if TCS.ChatVersion == Enum.ChatVersion.TextChatService then
			local chans = TCS:FindFirstChild("TextChannels")
			local ch = chans and chans:FindFirstChild("RBXGeneral")
			if ch and ch:IsA("TextChannel") then
				local esc = (string.gsub((string.gsub((string.gsub(line, "&", "&amp;")), "<", "&lt;")), ">", "&gt;"))
				pcall(function() (ch :: TextChannel):DisplaySystemMessage(('<font color="#FFC43D">%s</font>'):format(esc)) end)
			end
			return
		end
		task.spawn(function()
			local SG = game:GetService("StarterGui")
			for _ = 1, 10 do
				local ok = pcall(function()
					SG:SetCore("ChatMakeSystemMessage", { Text = line, Color = Color3.fromRGB(255, 196, 61), Font = Enum.Font.SourceSansBold, TextSize = 18 })
				end)
				if ok then return end
				task.wait(0.5)
			end
		end)
	end
	-- a gift for you (the owner's GIFT tab): one plain line at the top of the screen for a few seconds
	local function giftToast(text: string)
		local g = Instance.new("ScreenGui")
		g.Name = "DevGiftToast"; g.IgnoreGuiInset = true; g.DisplayOrder = 79; g.ResetOnSpawn = false
		local f = Instance.new("Frame")
		f.AnchorPoint = Vector2.new(0.5, 0)
		f.Position = UDim2.new(0.5, 0, 0, 118)
		f.Size = UDim2.fromOffset(0, 40)
		f.AutomaticSize = Enum.AutomaticSize.X
		f.BackgroundColor3 = Color3.fromRGB(16, 18, 22)
		f.BackgroundTransparency = 0.12
		f.BorderSizePixel = 0
		f.Parent = g
		local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0, 6); c.Parent = f
		local st = Instance.new("UIStroke"); st.Color = Color3.fromRGB(255, 196, 61); st.Transparency = 0.45; st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = f
		local pad = Instance.new("UIPadding"); pad.PaddingLeft = UDim.new(0, 18); pad.PaddingRight = UDim.new(0, 18); pad.Parent = f
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.AutomaticSize = Enum.AutomaticSize.X
		t.Size = UDim2.fromScale(0, 1)
		t.FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Bold)
		t.TextSize = 18
		t.TextColor3 = Color3.fromRGB(240, 242, 245)
		t.Text = string.sub(text, 1, 60)
		t.Parent = f
		g.Parent = me:WaitForChild("PlayerGui")
		task.delay(3.5, function()
			local TS = game:GetService("TweenService")
			TS:Create(f, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play()
			TS:Create(t, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
			TS:Create(st, TweenInfo.new(0.4), { Transparency = 1 }):Play()
			task.delay(0.45, function() g:Destroy() end)
		end)
	end
	local function flash(hold: number?)
		local g = Instance.new("ScreenGui")
		g.Name = "DevRedCardFlash"
		g.IgnoreGuiInset = true
		g.DisplayOrder = 80
		g.ResetOnSpawn = false
		local tint = Instance.new("Frame")
		tint.BackgroundColor3 = Color3.fromRGB(200, 20, 28)
		tint.BackgroundTransparency = 0.82
		tint.BorderSizePixel = 0
		tint.Size = UDim2.fromScale(1, 1)
		tint.Parent = g
		local card = Instance.new("Frame")
		card.Name = "Card"
		card.AnchorPoint = Vector2.new(0.5, 0.5)
		card.Position = UDim2.fromScale(0.5, 0.46)
		card.Size = UDim2.fromOffset(130, 182)
		card.Rotation = -8
		card.BackgroundColor3 = Color3.fromRGB(212, 30, 38)
		card.BorderSizePixel = 0
		card.Parent = g
		local cr = Instance.new("UICorner"); cr.CornerRadius = UDim.new(0, 10); cr.Parent = card
		local st = Instance.new("UIStroke"); st.Color = Color3.fromRGB(255, 236, 236); st.Thickness = 3; st.Transparency = 0.2; st.Parent = card
		local sc = Instance.new("UIScale"); sc.Scale = 0.3; sc.Parent = card
		g.Parent = me:WaitForChild("PlayerGui")
		local TS = game:GetService("TweenService")
		TS:Create(sc, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		task.delay(hold or 0.9, function()
			TS:Create(card, TweenInfo.new(0.35), { BackgroundTransparency = 1 }):Play()
			TS:Create(st, TweenInfo.new(0.35), { Transparency = 1 }):Play()
			TS:Create(tint, TweenInfo.new(0.35), { BackgroundTransparency = 1 }):Play()
			task.delay(0.4, function() g:Destroy() end)
		end)
	end
	-- (Studio photos: player attribute DevCardTest = seconds holds your own arm up with the card that long; DevFlashTest =
	-- seconds holds the target's red card flash)
	if RunService:IsStudio() then
		me:GetAttributeChangedSignal("DevCardTest"):Connect(function()
			local v = me:GetAttribute("DevCardTest")
			if type(v) == "number" and me.Character then task.spawn(pose, me.Character, v) end
		end)
		me:GetAttributeChangedSignal("DevFlashTest"):Connect(function()
			local v = me:GetAttribute("DevFlashTest")
			if type(v) == "number" then flash(v) end
		end)
	end
	if Fx then
		Fx.OnClientEvent:Connect(function(d: any)
			-- (a gift: the present plays it, GiftReveal.client; in a match it waits for a break, so the toast says it came)
			if type(d) == "table" and d.k == "gift" and type(d.text) == "string" then
				if me:GetAttribute("Zone") == "match" or type(d.items) ~= "table" then giftToast(d.text) end
				return
			end
			if type(d) == "table" and d.k == "giftchat" and type(d.text) == "string" then giftChat(d.text); return end
			-- (TEMP DEV: the owner lent you the powers, or it ended. one plain line at the top)
			if type(d) == "table" and d.k == "devaccess" then
				if d.on == true then
					local e = tonumber(d.ends) or 0
					giftToast(if e == 0 then "DEV ACCESS UNTIL YOU LEAVE  ·  F8" else ("DEV ACCESS UNTIL %s  ·  F8"):format(os.date("%H:%M", e)))
				else
					giftToast("DEV ACCESS ENDED")
				end
				return
			end
			if type(d) ~= "table" or d.k ~= "redcard" then return end
			local by = d.by
			local ch = typeof(by) == "Instance" and by:IsA("Player") and by.Character or nil
			local secs = if type(d.pose) == "number" then math.clamp(d.pose, 0.3, 3) else 1.2
			local id = if type(d.sound) == "string" then d.sound else ""
			if ch then
				task.spawn(pose, ch, secs)
				whistle(id, ch:FindFirstChild("Head") :: BasePart?)
			end
			if d.target == me then
				if not ch or (ch:FindFirstChild("Head") and me.Character and me.Character:FindFirstChild("Head")
					and ((ch.Head :: BasePart).Position - (me.Character.Head :: BasePart).Position).Magnitude > 120) then
					whistle(id, nil) -- (far from the owner: heard anyway, on you)
				end
				flash()
			end
		end)
	end
end

-- ------------------------------------------------------------------ the owner's only (and a friend's while the owner lends it)
-- TEMP DEV (19 Nov: "allow me to temp give command panel to friends exclude the gifting portion of it"): the server
-- puts DevTemp on a friend the owner lends the powers to (when it ends, os.time, or 0 = until they leave). their menu is
-- built the first time it comes, with the POWERS tab only; it closes and the DEV button goes when it ends, and comes
-- back if it's lent again. the server refuses a friend everything else whatever this side shows
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("OwnerDev", 30) :: RemoteFunction?
if not Remote then return end
local function call(...: any): any
	local args = table.pack(...)
	local ok, res = pcall(function() return (Remote :: RemoteFunction):InvokeServer(table.unpack(args, 1, args.n)) end)
	return if ok then res else nil
end
local creator = game.CreatorType == Enum.CreatorType.User and me.UserId > 0 and me.UserId == game.CreatorId
local hello = if creator or me:GetAttribute("DevTemp") ~= nil then call("hello") else nil
while type(hello) ~= "table" or (hello.owner ~= true and hello.temp ~= true) do
	me:GetAttributeChangedSignal("DevTemp"):Wait()
	if me:GetAttribute("DevTemp") ~= nil then hello = call("hello") end
end
local OWNER = hello.owner == true
local function lent(): boolean return OWNER or me:GetAttribute("DevTemp") ~= nil end
local function accessText(): string
	local e = me:GetAttribute("DevTemp")
	if type(e) ~= "number" then return "" end
	return if e == 0 then "dev access until you leave" else "dev access until " .. os.date("%H:%M", e)
end

local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local Body = require(J:WaitForChild("Body")) :: any
local Roster = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Roster")) :: any
local LoadoutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout", 30) :: RemoteFunction?

local function zone(): string return tostring(me:GetAttribute("Zone") or "hub") end
local function inMatch(): boolean return zone() == "match" end
local function typing(): boolean return UIS:GetFocusedTextBox() ~= nil end

-- ------------------------------------------------------------------ fly
local Fly = {}
do
	local lv: LinearVelocity? = nil
	local ao: AlignOrientation? = nil
	local on = false
	local controls: any = nil
	task.spawn(function()
		local ok, c = pcall(function()
			return (require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any) :: any):GetControls()
		end)
		if ok and type(c) == "table" then controls = c end
	end)
	local function parts(): (Humanoid?, BasePart?)
		local ch = me.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return nil, nil end
		return hum, root
	end
	function Fly.stop()
		if lv then lv:Destroy(); lv = nil end
		if ao then ao:Destroy(); ao = nil end
		if not on then return end
		on = false
		Body.flying = false
		local hum, root = parts()
		if hum then hum.PlatformStand = false end
		if root then
			local jm = root:FindFirstChild("JankMove")
			if jm and jm:IsA("LinearVelocity") then jm.Enabled = true end
			root.AssemblyLinearVelocity = root.AssemblyLinearVelocity * 0.2 -- (stops where you let go)
		end
	end
	local function start(root: BasePart, hum: Humanoid)
		local att = root:FindFirstChild("RootAttachment") :: Attachment?
		if not att then
			local a = Instance.new("Attachment")
			a.Name = "RootAttachment"
			a.Parent = root
			att = a
		end
		local v = Instance.new("LinearVelocity")
		v.Name = "JankDevFly"
		v.Attachment0 = att
		v.RelativeTo = Enum.ActuatorRelativeTo.World
		v.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
		v.MaxForce = math.huge
		v.VectorVelocity = Vector3.zero
		v.Parent = root
		local o = Instance.new("AlignOrientation")
		o.Name = "JankDevFlyTurn"
		o.Mode = Enum.OrientationAlignmentMode.OneAttachment
		o.Attachment0 = att
		o.RigidityEnabled = true
		o.CFrame = CFrame.lookAt(Vector3.zero, root.CFrame.LookVector)
		o.Parent = root
		lv, ao = v, o
		local jm = root:FindFirstChild("JankMove")
		if jm and jm:IsA("LinearVelocity") then jm.Enabled = false end -- (the movement script's own: it stands down)
		hum.PlatformStand = true
		Body.flying = true
		on = true
	end
	local function key(k: Enum.KeyCode): boolean return UIS:IsKeyDown(k) end
	local function padDown(k: Enum.KeyCode): boolean
		local ok, d = pcall(function() return UIS:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, k) end)
		return ok and d == true
	end
	RunService:BindToRenderStep("JankDevFly", Enum.RenderPriority.Camera.Value + 2, function()
		local speed = me:GetAttribute("DevFly")
		local hum, root = parts()
		if type(speed) ~= "number" or not hum or not root then Fly.stop(); return end
		if not on or not lv or not lv.Parent then
			Fly.stop()
			start(root, hum)
		end
		local cam = workspace.CurrentCamera
		if not cam or not lv or not ao then return end
		local mv = Vector3.zero
		if controls and not typing() then
			local ok, v = pcall(function() return controls:GetMoveVector() end)
			if ok and typeof(v) == "Vector3" then mv = v end
		end
		local dir = cam.CFrame:VectorToWorldSpace(mv)
		local up = 0
		if not typing() then
			if key(Enum.KeyCode.Space) or padDown(Enum.KeyCode.ButtonA) then up += 1 end
			if key(Enum.KeyCode.LeftControl) or key(Enum.KeyCode.C) or padDown(Enum.KeyCode.ButtonB) then up -= 1 end
		end
		local v = dir * speed + Vector3.new(0, up * speed, 0)
		if v.Magnitude > speed then v = v.Unit * speed end
		lv.VectorVelocity = v
		local lk = cam.CFrame.LookVector
		local flat = Vector3.new(lk.X, 0, lk.Z)
		if flat.Magnitude > 1e-3 then ao.CFrame = CFrame.lookAt(Vector3.zero, flat.Unit) end
		if not hum.PlatformStand then hum.PlatformStand = true end
	end)
	me.CharacterAdded:Connect(function() lv, ao, on = nil, nil, false; Body.flying = false end)
end

-- ------------------------------------------------------------------ noclip and run speed
do
	local saved: { [BasePart]: boolean } = {}
	RunService.Stepped:Connect(function()
		local ch = me.Character
		if me:GetAttribute("DevNoclip") == true and ch then
			for _, d in ch:GetDescendants() do
				if d:IsA("BasePart") and d.CanCollide then
					saved[d] = true
					d.CanCollide = false
				end
			end
		elseif next(saved) then
			for part in saved do if part.Parent then part.CanCollide = true end end
			table.clear(saved)
		end
	end)
	local function speed()
		local s = me:GetAttribute("DevSpeed")
		Body.devSpeed = if type(s) == "number" then math.clamp(s, 1, 4) else 1
	end
	me:GetAttributeChangedSignal("DevSpeed"):Connect(speed)
	me:GetAttributeChangedSignal("Zone"):Connect(speed)
	speed()
end

-- ------------------------------------------------------------------ invisible: your ghost
-- the server made every part of you fully see-through (DevWas = what it was); here, on your screen only, you're a faint
-- ghost. the server's own write puts each one back when it ends
do
	local function ghost(d: Instance)
		if me:GetAttribute("DevInvisible") ~= true then return end
		local was = d:GetAttribute("DevWas")
		if type(was) ~= "number" or was >= 1 then return end
		if d:IsA("BasePart") or d:IsA("Decal") then (d :: any).Transparency = 0.72 + 0.28 * was end
	end
	local function all()
		local ch = me.Character
		if ch then for _, d in ch:GetDescendants() do ghost(d) end end
	end
	local watched: { [Instance]: boolean } = setmetatable({}, { __mode = "k" }) :: any
	local function watch(ch: Model)
		if watched[ch] then return end
		watched[ch] = true
		ch.DescendantAdded:Connect(function(d) task.defer(ghost, d) end)
	end
	me:GetAttributeChangedSignal("DevInvisible"):Connect(function() task.delay(0.2, all) end)
	me.CharacterAdded:Connect(function(ch) watch(ch); task.delay(0.5, all) end)
	if me.Character then watch(me.Character) end
	task.spawn(function() -- (a part whose DevWas came after it: once a second while it lasts)
		while true do
			task.wait(1)
			if me:GetAttribute("DevInvisible") == true then all() end
		end
	end)
end

-- ------------------------------------------------------------------ the menu
local gui = T.new("ScreenGui", { Name = "OwnerDev", ResetOnSpawn = false, DisplayOrder = 61, IgnoreGuiInset = true, Enabled = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local scaled = T.scaled(gui)
local plate = T.plate(scaled, "Panel", UDim2.new(0.5, -450, 0.5, -255), UDim2.fromOffset(900, 510))
plate.BackgroundTransparency = 0.08

local title = T.text(plate, "Title", "DEV", 18, T.TEXT, T.FONT_TITLE)
title.Position = UDim2.fromOffset(18, 12); title.Size = UDim2.fromOffset(200, 26)
local status = T.text(plate, "Status", "", 13, T.MUTED)
status.Position = UDim2.fromOffset(18, 38); status.Size = UDim2.fromOffset(560, 18)
local note = T.text(plate, "Note", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Left)
note.Position = UDim2.new(0, 18, 1, -30); note.Size = UDim2.new(1, -36, 0, 18)

local function button(parent: Instance, name: string, text: string, pos: UDim2, w: number, h: number?): TextButton
	local b = T.new("TextButton", {
		Name = name, Text = text, FontFace = T.FONT_BOLD, TextSize = 13, AutoButtonColor = true, TextColor3 = T.TEXT,
		BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, Position = pos, Size = UDim2.fromOffset(w, h or 28),
	}, parent)
	T.corner(b, 4)
	return b
end
local function lit(b: TextButton, on: boolean)
	b.BackgroundColor3 = if on then T.ACCENT else T.CARD_HI
	b.TextColor3 = if on then T.INK else T.TEXT
end
local function said(res: any, fallback: string)
	if type(res) == "table" and res.ok then note.Text = tostring(res.did or fallback)
	else note.Text = "refused: " .. tostring(if type(res) == "table" and res.why then res.why else "no answer") end
end

local close = button(plate, "Close", "CLOSE", UDim2.new(1, -86, 0, 14), 70)
close.Modal = true -- (frees the mouse from first person while the menu is up)

-- the left half: me
local ME_X, ME_W = 18, 360
local function label(parent: Instance, name: string, text: string, x: number, y: number, w: number): TextLabel
	local l = T.text(parent, name, text, 12, T.MUTED, T.FONT_BOLD)
	l.Position = UDim2.fromOffset(x, y); l.Size = UDim2.fromOffset(w, 16)
	return l
end
label(plate, "MeHead", "ME", ME_X, 66, 100)

local flyB = button(plate, "Fly", "FLY", UDim2.fromOffset(ME_X, 86), 84)
local noclipB = button(plate, "Noclip", "NOCLIP", UDim2.fromOffset(ME_X + 92, 86), 84)
local invisB = button(plate, "Invisible", "INVISIBLE", UDim2.fromOffset(ME_X + 184, 86), 84)
local armsB = button(plate, "Arms", "WEAPONS", UDim2.fromOffset(ME_X + 276, 86), 84)

-- a slider: a track you click or drag (mouse, touch), and - / + (a pad, or a fine step)
type Slider = { set: (number) -> (), value: () -> number }
local function slider(name: string, text: string, y: number, lo: number, hi: number, step: number, fmt: string, send: (number) -> ()): Slider
	label(plate, name .. "Label", text, ME_X, y + 6, 90)
	local minus = button(plate, name .. "Minus", "-", UDim2.fromOffset(ME_X + 92, y), 28)
	local track = T.new("TextButton", { Name = name .. "Track", Text = "", AutoButtonColor = false, BackgroundColor3 = T.TRACK, BorderSizePixel = 0,
		Position = UDim2.fromOffset(ME_X + 126, y + 11), Size = UDim2.fromOffset(150, 6), Selectable = false }, plate)
	T.corner(track, 3)
	local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, track)
	T.corner(fill, 3)
	local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.TEXT, BorderSizePixel = 0,
		Position = UDim2.fromScale(0, 0.5), Size = UDim2.fromOffset(14, 14) }, track)
	T.corner(knob, 7)
	local plus = button(plate, name .. "Plus", "+", UDim2.fromOffset(ME_X + 282, y), 28)
	local val = T.text(plate, name .. "Value", "", 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	val.Position = UDim2.fromOffset(ME_X + 312, y + 5); val.Size = UDim2.fromOffset(48, 18)
	local v = lo
	local function draw()
		local a = (v - lo) / (hi - lo)
		fill.Size = UDim2.fromScale(a, 1)
		knob.Position = UDim2.fromScale(a, 0.5)
		val.Text = fmt:format(v)
	end
	local function snap(x: number): number return math.clamp(math.floor((x - lo) / step + 0.5) * step + lo, lo, hi) end
	local dragging: InputObject? = nil
	local function fromX(x: number)
		local a = math.clamp((x - track.AbsolutePosition.X) / math.max(1, track.AbsoluteSize.X), 0, 1)
		v = snap(lo + a * (hi - lo))
		draw()
	end
	track.InputBegan:Connect(function(io: InputObject)
		if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
			dragging = io
			fromX(io.Position.X)
		end
	end)
	UIS.InputChanged:Connect(function(io: InputObject)
		if not dragging then return end
		if io.UserInputType == Enum.UserInputType.MouseMovement or io == dragging then fromX(io.Position.X) end
	end)
	UIS.InputEnded:Connect(function(io: InputObject)
		if dragging and (io == dragging or io.UserInputType == Enum.UserInputType.MouseButton1) then
			dragging = nil
			send(v)
		end
	end)
	minus.Activated:Connect(function() v = snap(v - step); draw(); send(v) end)
	plus.Activated:Connect(function() v = snap(v + step); draw(); send(v) end)
	draw()
	return { set = function(x: number) if not dragging then v = snap(x); draw() end end, value = function() return v end }
end

local flySpeed = slider("FlySpeed", "FLY SPEED", 124, 20, 300, 10, "%d", function(x) said(call("set", "flySpeed", x), "fly speed " .. x) end)
local runSpeed = slider("RunSpeed", "RUN SPEED", 160, 1, 4, 0.25, "%.2fx", function(x) said(call("set", "speed", x), ("run speed %.2fx"):format(x)) end)

-- weapons: every live one, by slot. a pick goes into the try layer (never saved): in the hub only with WEAPONS IN HUB on
label(plate, "WeaponsHead", "GIVE ME A WEAPON", ME_X, 200, 200)
local wlist = T.new("ScrollingFrame", {
	Name = "Weapons", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(ME_X, 220), Size = UDim2.fromOffset(ME_W, 252),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(wlist, 4)
T.new("UIGridLayout", { CellSize = UDim2.fromOffset(110, 26), CellPadding = UDim2.fromOffset(6, 6), SortOrder = Enum.SortOrder.LayoutOrder }, wlist)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6), PaddingBottom = UDim.new(0, 6) }, wlist)
local weaponButtons: { [string]: TextButton } = {}
do
	local order = 0
	for _, slot in Roster.SLOTS do
		for _, e in Roster.list do
			-- (a coming-soon weapon that has a weapon row is here too, for tests: the server lets DevArms arm it. "(soon)")
			local soon = not e.live and (ReplicatedStorage:WaitForChild("Jankfire"):FindFirstChild("Weapons") ~= nil) and (require(ReplicatedStorage.Jankfire.Weapons) :: any).list[e.id] ~= nil
			if e.slot ~= slot or not (e.live or soon) then continue end
			order += 1
			local b = T.new("TextButton", {
				Name = "W_" .. e.id, Text = string.upper(e.name) .. (if soon then " (soon)" else ""), FontFace = T.FONT_BOLD, TextSize = 11, TextScaled = false,
				TextTruncate = Enum.TextTruncate.AtEnd, AutoButtonColor = true, TextColor3 = T.TEXT, BackgroundColor3 = T.CARD_HI,
				BorderSizePixel = 0, LayoutOrder = order,
			}, wlist)
			T.corner(b, 4)
			local bar = T.new("Frame", { Name = "Slot", BackgroundColor3 = e.color or T.DIM, BorderSizePixel = 0, Size = UDim2.new(0, 3, 1, -8), Position = UDim2.fromOffset(3, 4) }, b)
			T.corner(bar, 1)
			weaponButtons[e.id] = b
			b.Activated:Connect(function()
				if not LoadoutR then note.Text = "no loadout remote"; return end
				local z = zone()
				if z ~= "training" and z ~= "playground" and me:GetAttribute("DevArms") ~= true then
					local r = call("set", "arms", true)
					if type(r) ~= "table" or not r.ok then said(r, ""); return end
				end
				local ok, okP, why = pcall(function() return (LoadoutR :: RemoteFunction):InvokeServer("pick", e.slot, e.id) end)
				note.Text = if ok and okP then ("%s in hand (key %d)"):format(e.name, (table.find(Roster.SLOTS, e.slot) or 1))
					else "refused: " .. tostring(if ok then why else okP)
			end)
		end
	end
end

-- the right half: everyone else
local PL_X, PL_W = 398, 484
label(plate, "PlayersHead", "PLAYERS", PL_X, 66, 100)
local hint = T.text(plate, "Hint", "X  fling  ·  Z  freeze / let go  ·  Y  red card  (whoever you look at)", 12, T.DIM, T.FONT, Enum.TextXAlignment.Right)
hint.Position = UDim2.fromOffset(PL_X + 60, 66); hint.Size = UDim2.fromOffset(PL_W - 60 - 136, 16)
-- AIM KEYS (19 Nov: X is the grapple's REEL IN too): X / Z / Y do nothing for the dev menu until this is on. it stays on
-- until you turn it off (this session), and a small DEV KEYS ON chip shows under the DEV button while it is
local aimKeys = false
local keysChip: TextLabel? = nil -- (made with the DEV button, below)
local aimB = button(plate, "AimKeys", "AIM KEYS: OFF", UDim2.fromOffset(PL_X + PL_W - 128, 62), 128, 24)
aimB.TextSize = 11
local function drawAim()
	lit(aimB, aimKeys)
	aimB.Text = if aimKeys then "AIM KEYS: ON" else "AIM KEYS: OFF"
	if keysChip then keysChip.Visible = aimKeys end
end
aimB.Activated:Connect(function()
	aimKeys = not aimKeys
	drawAim()
	note.Text = if aimKeys then "aim keys on: X flings, Z freezes, Y shows a red card to whoever you look at" else "aim keys off: X, Z and Y are the game's again"
end)
local plist = T.new("ScrollingFrame", {
	Name = "Players", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(PL_X, 86), Size = UDim2.fromOffset(PL_W, 350),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(plist, 4)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, plist)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 6) }, plist)
local unfreezeB = button(plate, "UnfreezeAll", "UNFREEZE EVERYONE", UDim2.fromOffset(PL_X, 444), 150)
local emptyB = button(plate, "EmptyJail", "EMPTY THE JAIL", UDim2.fromOffset(PL_X + 158, 444), 130)
local offB = button(plate, "AllOff", "ALL MY POWERS OFF", UDim2.fromOffset(PL_X + 296, 444), 150)


local open = false
local refreshPlayers: () -> ()
local function drawMe()
	local fly = me:GetAttribute("DevFly")
	lit(flyB, type(fly) == "number")
	flyB.Text = if type(fly) == "number" then "FLY: ON" else "FLY: OFF"
	local nc = me:GetAttribute("DevNoclip") == true
	lit(noclipB, nc)
	noclipB.Text = if nc then "NOCLIP: ON" else "NOCLIP: OFF"
	local arms = me:GetAttribute("DevArms") == true
	lit(armsB, arms)
	armsB.Text = if arms then "WEAPONS: ON" else "WEAPONS"
	local inv = me:GetAttribute("DevInvisible") == true
	lit(invisB, inv)
	invisB.Text = if inv then "HIDDEN: ON" else "INVISIBLE"
	local fs = me:GetAttribute("DevFlySpeed")
	if type(fs) == "number" then flySpeed.set(fs) end
	local rs = me:GetAttribute("DevSpeed")
	runSpeed.set(if type(rs) == "number" then rs else 1)
	local z = zone()
	local words = { hub = "HUB", training = "TRAINING", playground = "PLAYGROUND", staging = "MAP ROOM", match = "MATCH" }
	local how = if me:GetAttribute("DevOn") == true then "anti-cheat leaves you alone" else "no powers on"
	if z == "match" then how = if me:GetAttribute("MatchDev") ~= nil then "this match counts for nothing now" else "a power used here makes this match count for nothing" end
	status.Text = ("%s%s  ·  %s"):format(if OWNER then "" else string.upper(accessText()) .. "  ·  ", words[z] or string.upper(z), how)
end
for _, a in { "DevFly", "DevNoclip", "DevArms", "DevFlySpeed", "DevSpeed", "DevOn", "Zone", "MatchDev", "DevInvisible", "DevTemp" } do
	me:GetAttributeChangedSignal(a):Connect(function() if open then drawMe() end end)
end

flyB.Activated:Connect(function() said(call("set", "fly", type(me:GetAttribute("DevFly")) ~= "number"), "fly") end)
noclipB.Activated:Connect(function() said(call("set", "noclip", me:GetAttribute("DevNoclip") ~= true), "noclip") end)
armsB.Activated:Connect(function() said(call("set", "arms", me:GetAttribute("DevArms") ~= true), "weapons") end)
invisB.Activated:Connect(function() said(call("set", "invis", me:GetAttribute("DevInvisible") ~= true), "invisible") end)
emptyB.Activated:Connect(function() said(call("emptyJail"), "jail emptied"); task.defer(refreshPlayers) end)
unfreezeB.Activated:Connect(function() said(call("unfreezeAll"), "everyone let go"); task.defer(refreshPlayers) end)
offB.Activated:Connect(function() said(call("set", "off"), "all off") end)

local function cell(parent: Instance, name: string, text: string, x: number, w: number, color: Color3?, font: Font?)
	local l = T.text(parent, name, text, 12, color or T.TEXT, font or T.FONT, Enum.TextXAlignment.Left)
	l.Position = UDim2.fromOffset(x, 0); l.Size = UDim2.new(0, w, 1, 0)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	return l
end
refreshPlayers = function()
	if not open then return end
	local res = call("players")
	for _, c in plist:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	if type(res) ~= "table" or not res.ok or type(res.players) ~= "table" then return end
	if #res.players == 0 then
		local row = T.new("Frame", { Name = "Empty", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 26) }, plist)
		cell(row, "Text", "nobody else here", 4, 300, T.DIM)
		return
	end
	for i, r in res.players do
		local row = T.new("Frame", { Name = "Row_" .. tostring(r.user or i), BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 30), LayoutOrder = i }, plist)
		T.corner(row, 4)
		-- (TEMP DEV: a friend's buttons do nothing on the owner, another friend with dev, or someone the owner holds; the
		-- server refuses those anyway)
		local away = not OWNER and (r.owner == true or r.temp ~= nil or r.held == true)
		cell(row, "Name", tostring(r.name), 8, 96, T.TEXT, T.FONT_BOLD)
		cell(row, "Zone", if r.jailed then "JAILED" elseif r.frozen then "FROZEN" elseif r.owner then "OWNER" elseif r.temp ~= nil then "DEV"
			else string.upper(tostring(r.zone)), 104, 64, if r.frozen or r.jailed or r.owner or r.temp ~= nil then T.ACCENT else T.MUTED)
		local x = 170
		local function act(name: string, text: string, w: number, fn: () -> ())
			local b = button(row, name, text, UDim2.fromOffset(x, 3), w, 24)
			b.TextSize = 11
			x += w + 4
			if away then b.AutoButtonColor = false; b.TextColor3 = T.DIM end
			b.Activated:Connect(function() if not away then fn(); task.delay(0.2, refreshPlayers) end end)
		end
		act("Fling", "FLING", 44, function() said(call("fling", r.ref), "flung") end)
		act("Freeze", if r.frozen then "LET GO" else "FREEZE", 52, function() said(call("freeze", r.ref, not r.frozen), "done") end)
		act("Goto", "GO TO", 40, function() said(call("goto", r.ref), "done") end)
		act("Bring", "BRING", 40, function() said(call("bring", r.ref), "done") end)
		act("Jail", if r.jailed then "FREE" else "JAIL", 40, function() said(call(if r.jailed then "release" else "jail", r.ref), "done") end)
		act("RedCard", "RED CARD", 60, function() said(call("redcard", r.ref), "done") end)
		local rc = row:FindFirstChild("RedCard") :: TextButton?
		if rc then rc.BackgroundColor3 = Color3.fromRGB(150, 34, 40) end
	end
end

-- ------------------------------------------------------------------ the GIFT tab
-- (18 Nov, the owner: "let me gift people stuff! bundles, cases bags cans at any quantity coins vip etc"): pick who
-- gets it (anyone in the server, or you), then what: containers in any number, a bundle or skin set, one item from the
-- searchable list, coins, Brass, Crate Tickets, VIP. the server checks and gives each one (OwnerDev.server, "gift")
-- (19 Nov, the owner: "allow me to also give people xp, I want to be able to unlock stuff for my friends!!"): XP
-- (account XP or a level, weapon mastery XP or a mastery level) and UNLOCKS (one weapon, the 4 premium ones too, or
-- every weapon). they go through the normal levels on the server (Stats.gift, Purchases.unlockWeapons)
local Gift: any = { shown = false, refresh = function() end }
do
	local Shop = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Shop")) :: any
	local LootTable = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("LootTable")) :: any
	local tabPowers = button(plate, "TabPowers", "POWERS", UDim2.fromOffset(96, 12), 90)
	local tabGift = button(plate, "TabGift", "GIFT", UDim2.fromOffset(192, 12), 90)
	local tabAnnounce = button(plate, "TabAnnounce", "ANNOUNCE", UDim2.fromOffset(288, 12), 100)
	local tabFriends = button(plate, "TabFriends", "FRIENDS", UDim2.fromOffset(394, 12), 96)
	local keep = { [title] = true, [status] = true, [note] = true, [close] = true, [tabPowers] = true, [tabGift] = true, [tabAnnounce] = true, [tabFriends] = true }
	local powersKids: { GuiObject } = {}
	for _, c in plate:GetChildren() do
		if c:IsA("GuiObject") and not keep[c] then table.insert(powersKids, c) end
	end
	if not OWNER then
		-- (TEMP DEV: the POWERS tab only, without UNFREEZE EVERYONE / EMPTY THE JAIL, which would undo the owner's too)
		for _, b in { tabGift, tabAnnounce, tabFriends, unfreezeB, emptyB } do
			b.Visible = false
			local i = table.find(powersKids, b)
			if i then table.remove(powersKids, i) end
		end
	end
	local page = T.new("Frame", { Name = "Gift", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 60), Size = UDim2.new(1, 0, 1, -96), Visible = false }, plate)

	local function list(parent: Instance, name: string, pos: UDim2, size: UDim2): ScrollingFrame
		local l = T.new("ScrollingFrame", {
			Name = name, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0, Position = pos, Size = size,
			CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
		}, parent)
		T.corner(l, 4)
		T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, l)
		T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 6) }, l)
		return l
	end
	local function clear(l: Instance) for _, c in l:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end end
	local function box(parent: Instance, name: string, text: string, pos: UDim2, w: number, hint: string?): TextBox
		local b = T.new("TextBox", {
			Name = name, Text = text, PlaceholderText = hint or "", FontFace = T.FONT_BOLD, TextSize = 13, TextColor3 = T.TEXT,
			PlaceholderColor3 = T.DIM, BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, ClearTextOnFocus = false,
			Position = pos, Size = UDim2.fromOffset(w, 28),
		}, parent)
		T.corner(b, 4)
		return b
	end

	-- who gets it
	label(page, "ToHead", "TO", 18, 0, 100)
	local toList = list(page, "To", UDim2.fromOffset(18, 20), UDim2.fromOffset(200, 318))
	-- (19 Nov, round 4: "gift everyone"): EVERYONE HERE (this server) and ALL SERVERS (every live server): the players
	-- there right now, once each; nobody who joins later. ALL SERVERS asks for a second press
	local everyNote = T.text(page, "EveryoneNote", "EVERYONE = the players there right now, once each. Anyone joining later gets nothing.", 11, T.DIM, T.FONT, Enum.TextXAlignment.Left)
	everyNote.Position = UDim2.fromOffset(18, 342); everyNote.Size = UDim2.fromOffset(200, 48)
	everyNote.TextWrapped = true; everyNote.TextYAlignment = Enum.TextYAlignment.Top
	local to: any = me -- (a Player, or "server" / "all")
	local onTo: { () -> () } = {} -- (pages that show something about the receiver: XP, UNLOCKS)
	local function drawTo()
		clear(toList)
		local people: { any } = { "server", "all", me }
		for _, q in Players:GetPlayers() do if q ~= me then table.insert(people, q) end end
		if not table.find(people, to) then to = me end
		for i, q in people do
			local name = if q == "server" then "EVERYONE HERE" elseif q == "all" then "ALL SERVERS" elseif q == me then "YOU" else q.DisplayName
			local b = button(toList, "To_" .. (if type(q) == "string" then q else tostring(q.UserId)), name, UDim2.new(), 180, 28)
			b.LayoutOrder = i
			b.TextXAlignment = Enum.TextXAlignment.Left
			T.new("UIPadding", { PaddingLeft = UDim.new(0, 10) }, b)
			lit(b, q == to)
			if type(q) == "string" and q ~= to then b.TextColor3 = T.ACCENT end
			b.Activated:Connect(function()
				to = q
				drawTo()
				for _, fn in onTo do task.spawn(fn) end
			end)
		end
	end
	local armed: { key: string, t: number }? = nil
	local function give(kind: string, id: string?, n: number?, what: string)
		local r
		if to == "server" or to == "all" then
			local key = ("%s|%s|%s|%s"):format(to, kind, tostring(id), tostring(n))
			if to == "all" and not (armed and armed.key == key and os.clock() - armed.t < 5) then
				armed = { key = key, t = os.clock() }
				note.Text = ("ALL SERVERS: press GIVE again to send %s to everyone in every server"):format(string.upper(what))
				return
			end
			armed = nil
			r = call("giftAll", to, { kind = kind, id = id, n = n })
		else
			r = call("gift", to, { kind = kind, id = id, n = n })
		end
		if type(r) == "table" and r.ok then note.Text = tostring(r.did or what)
		else note.Text = ("%s: %s"):format(what, tostring(if type(r) == "table" and r.why then r.why else "no answer")) end
	end

	-- what: the kinds
	local KX, KW = 232, 650
	local kinds = { "CONTAINERS", "BUNDLES", "ITEMS", "CURRENCY", "VIP", "XP", "UNLOCKS" }
	local kindBtn: { [string]: TextButton } = {}
	local kindPage: { [string]: Frame } = {}
	for i, k in kinds do
		kindBtn[k] = button(page, "Kind_" .. k, k, UDim2.fromOffset(KX + (i - 1) * 94, 14), 88)
		kindPage[k] = T.new("Frame", { Name = "Page_" .. k, BackgroundTransparency = 1, Position = UDim2.fromOffset(KX, 52), Size = UDim2.fromOffset(KW, 338), Visible = false }, page)
	end

	-- containers: which, how many
	do
		local P = kindPage.CONTAINERS
		local which = "crate"
		local cBtn: { [string]: TextButton } = {}
		-- (the Crate, the Duffel Bag and the six spray sets, four to a row, 20 Nov. the first Spray Can isn't given any more)
		local kinds = LootTable.SOLD or { "crate", "bag", "spray" }
		local CW = math.floor((KW - 30) / 4)
		for i, id in kinds do
			local c = LootTable.CONTAINERS[id]
			local word = if c.base == "spray" then string.upper(c.set) else string.upper(c.name)
			cBtn[id] = button(P, "C_" .. id, word, UDim2.fromOffset(((i - 1) % 4) * (CW + 10), math.floor((i - 1) / 4) * 40), CW, 34)
		end
		local DY = 40 * (math.ceil(#kinds / 4) - 1) -- (the rows past the first push the rest down)
		local function drawC() for id, b in cBtn do lit(b, id == which) end end
		for id, b in cBtn do b.Activated:Connect(function() which = id; drawC() end) end
		drawC()
		label(P, "HowMany", "HOW MANY (1 TO 999)", 0, 54 + DY, 200)
		local nBox = box(P, "Count", "1", UDim2.fromOffset(40, 76 + DY), 90)
		local minus = button(P, "Minus", "-", UDim2.fromOffset(0, 76 + DY), 32)
		local plus = button(P, "Plus", "+", UDim2.fromOffset(138, 76 + DY), 32)
		local function n(): number return math.clamp(math.floor(tonumber(nBox.Text) or 1), 1, 999) end
		minus.Activated:Connect(function() nBox.Text = tostring(math.max(1, n() - 1)) end)
		plus.Activated:Connect(function() nBox.Text = tostring(math.min(999, n() + 1)) end)
		for i, q in { 1, 5, 10, 50, 100 } do
			local b = button(P, "Q" .. q, tostring(q), UDim2.fromOffset(186 + (i - 1) * 50, 76 + DY), 44)
			b.Activated:Connect(function() nBox.Text = tostring(q) end)
		end
		local go = button(P, "Give", "GIVE", UDim2.fromOffset(0, 124 + DY), 170, 34)
		lit(go, true)
		go.Activated:Connect(function()
			local c = LootTable.CONTAINERS[which]
			give("container", which, n(), ("%d %s"):format(n(), if n() == 1 then c.name else c.plural))
		end)
	end

	-- bundles and skin sets, whole
	do
		local L = list(kindPage.BUNDLES, "List", UDim2.new(), UDim2.fromOffset(KW, 338))
		local all = {}
		for _, b in Shop.bundles do table.insert(all, b) end
		for _, s in Shop.sets or {} do if not table.find(all, s) then table.insert(all, s) end end
		for i, o in all do
			local row = T.new("Frame", { Name = "B_" .. o.id, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 30), LayoutOrder = i }, L)
			T.corner(row, 4)
			local t = T.text(row, "Name", string.upper(o.name), 12, T.TEXT, T.FONT_BOLD)
			t.Position = UDim2.fromOffset(8, 0); t.Size = UDim2.new(1, -200, 1, 0)
			local k = T.text(row, "Kind", if o.set then "SKIN SET" else "BUNDLE", 11, T.MUTED, T.FONT_BOLD)
			k.Position = UDim2.new(1, -190, 0, 0); k.Size = UDim2.fromOffset(100, 30)
			local g = button(row, "Give", "GIVE", UDim2.new(1, -78, 0, 3), 70, 24)
			g.TextSize = 11
			g.Activated:Connect(function() give("bundle", o.id, 1, o.name) end)
		end
	end

	-- single items, searchable (wraps and hats go on every gun)
	do
		local P = kindPage.ITEMS
		local search = box(P, "Search", "", UDim2.fromOffset(0, 0), KW, "search: a name, or wrap / hat / skin / emote ...")
		local L = list(P, "List", UDim2.fromOffset(0, 36), UDim2.fromOffset(KW, 302))
		local items: { any }? = nil
		local function all(): { any }
			if items then return items end
			local out, seen = {}, {}
			for _, c in { "crate", "bag", "spray" } do
				local ok, rows = pcall(LootTable.cosmetics, c)
				if ok and type(rows) == "table" then
					for _, it in rows do
						local key = it.type .. ":" .. it.id
						if not seen[key] then
							seen[key] = true
							table.insert(out, { key = key, name = tostring(it.name), type = it.type, rarity = tostring(it.rarity),
								hay = string.lower(tostring(it.name) .. " " .. it.type .. " " .. tostring(it.rarity) .. " " .. tostring(it.weapon or "")) })
						end
					end
				end
			end
			table.sort(out, function(a, b) return a.name < b.name end)
			items = out
			return out
		end
		local function draw()
			clear(L)
			local q = string.lower(search.Text)
			local n = 0
			for _, it in all() do
				if q ~= "" and not string.find(it.hay, q, 1, true) then continue end
				n += 1
				if n > 80 then break end
				local row = T.new("Frame", { Name = "I_" .. it.key, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 28), LayoutOrder = n }, L)
				T.corner(row, 4)
				local t = T.text(row, "Name", string.upper(it.name), 12, T.TEXT, T.FONT_BOLD)
				t.Position = UDim2.fromOffset(8, 0); t.Size = UDim2.new(1, -290, 1, 0); t.TextTruncate = Enum.TextTruncate.AtEnd
				local k = T.text(row, "Kind", string.upper((LootTable.TYPE_NAMES and LootTable.TYPE_NAMES[it.type]) or it.type) .. "  ·  " .. string.upper(it.rarity), 11, T.MUTED, T.FONT_BOLD)
				k.Position = UDim2.new(1, -280, 0, 0); k.Size = UDim2.fromOffset(196, 28)
				local g = button(row, "Give", "GIVE", UDim2.new(1, -78, 0, 2), 70, 24)
				g.TextSize = 11
				g.Activated:Connect(function() give("item", it.key, 1, it.name) end)
			end
			if n == 0 then
				local row = T.new("Frame", { Name = "None", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 28) }, L)
				local t = T.text(row, "Text", "nothing matches", 12, T.DIM)
				t.Position = UDim2.fromOffset(8, 0); t.Size = UDim2.new(1, -16, 1, 0)
			end
		end
		search:GetPropertyChangedSignal("Text"):Connect(draw)
		Gift.items = draw
	end

	-- coins, Brass, Crate Tickets: any amount
	do
		local P = kindPage.CURRENCY
		for i, c in { { "brass", "COINS" }, { "tickets", "CRATE TICKETS" } } do
			local y = (i - 1) * 56
			label(P, "L_" .. c[1], c[2], 0, y + 6, 160)
			local b = box(P, "N_" .. c[1], "", UDim2.fromOffset(170, y), 160, "how many")
			local g = button(P, "Give_" .. c[1], "GIVE", UDim2.fromOffset(340, y), 100)
			g.Activated:Connect(function()
				local n = tonumber(b.Text)
				if not n or n < 1 then note.Text = "type how many"; return end
				give(c[1], nil, math.floor(n), c[2])
			end)
		end
	end

	-- VIP for good (the Robux weapons are on UNLOCKS now)
	do
		local P = kindPage.VIP
		local g = button(P, "GiveVip", "GIVE VIP", UDim2.fromOffset(0, 0), 170, 34)
		lit(g, true)
		g.Activated:Connect(function() give("vip", nil, 1, "VIP") end)
		local t = T.text(P, "WeaponsMoved", "The premium (Robux) weapons are on UNLOCKS.", 12, T.DIM, T.FONT, Enum.TextXAlignment.Left)
		t.Position = UDim2.fromOffset(0, 48); t.Size = UDim2.fromOffset(400, 18)
	end

	local Unlocks = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Unlocks")) :: any
	local Mastery = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Mastery")) :: any
	local Ranks = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Ranks")) :: any
	local function commas(n: number): string
		local r = string.reverse((string.gsub(string.reverse(tostring(math.floor(n))), "(%d%d%d)", "%1,")))
		return (string.gsub(r, "^,", ""))
	end
	local function numOf(b: TextBox): number?
		local n = tonumber((string.gsub(b.Text, "[,%s]", "")))
		return if n and n >= 1 then math.floor(n) else nil
	end
	local function one(): Player? return if typeof(to) == "Instance" then to :: Player else nil end

	-- XP: account XP or a level; weapon mastery XP or a mastery level. a level only goes up
	do
		local P = kindPage.XP
		label(P, "AccHead", "ACCOUNT XP", 0, 0, 200)
		local xpBox = box(P, "XpN", "", UDim2.fromOffset(0, 20), 140, "how much XP")
		local giveXp = button(P, "GiveXp", "GIVE XP", UDim2.fromOffset(148, 20), 110)
		lit(giveXp, true)
		for i, q in { 100, 1000, 10000, 100000 } do
			local b = button(P, "XQ" .. q, commas(q), UDim2.fromOffset(270 + (i - 1) * 70, 20), 64)
			b.Activated:Connect(function() xpBox.Text = tostring(q) end)
		end
		label(P, "LvHead", "SET LEVEL (2 TO 500: ONLY UP)", 0, 58, 260)
		local lvBox = box(P, "LvN", "", UDim2.fromOffset(0, 78), 140, "level")
		local setLv = button(P, "SetLevel", "SET LEVEL", UDim2.fromOffset(148, 78), 110)
		lit(setLv, true)
		local now = T.text(P, "Now", "", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Left)
		now.Position = UDim2.fromOffset(270, 78); now.Size = UDim2.fromOffset(380, 28)
		giveXp.Activated:Connect(function()
			local n = numOf(xpBox)
			if not n then note.Text = "type how much XP"; return end
			give("xp", nil, n, commas(n) .. " XP")
		end)
		setLv.Activated:Connect(function()
			local n = numOf(lvBox)
			if not n or n < 2 then note.Text = "type a level, 2 or more"; return end
			give("level", nil, n, "level " .. n)
		end)

		label(P, "MHead", "WEAPON MASTERY", 0, 122, 200)
		local wl = list(P, "Weapons", UDim2.fromOffset(0, 142), UDim2.fromOffset(200, 196))
		local wid: string? = nil
		local wBtn: { [string]: TextButton } = {}
		local wName = T.text(P, "Weapon", "pick a weapon", 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Left)
		wName.Position = UDim2.fromOffset(216, 142); wName.Size = UDim2.fromOffset(434, 22)
		local mxBox = box(P, "MxN", "", UDim2.fromOffset(216, 170), 140, "mastery XP")
		local giveMx = button(P, "GiveMastery", "GIVE MASTERY XP", UDim2.fromOffset(364, 170), 160)
		local mlBox = box(P, "MlN", "", UDim2.fromOffset(216, 208), 140, "mastery level")
		local setMl = button(P, "SetMastery", "SET MASTERY LEVEL", UDim2.fromOffset(364, 208), 160)
		lit(giveMx, true); lit(setMl, true)
		local camoNames = {}
		for i, c in Mastery.CAMOS do
			table.insert(camoNames, c.level .. " " .. string.lower(c.name))
			local b = button(P, "ML" .. c.level, ("LV %d · %s"):format(c.level, c.name), UDim2.fromOffset(216 + (i - 1) * 110, 246), 104)
			b.TextSize = 11
			b.Activated:Connect(function() mlBox.Text = tostring(c.level) end)
		end
		local info = T.text(P, "Info", ("Through the normal levels: the level-up toasts, the weapons a level opens and the camos at their mastery levels (%s) come as usual. A level only goes up. Ranked never sees it."):format(table.concat(camoNames, ", ")), 11, T.DIM, T.FONT, Enum.TextXAlignment.Left)
		info.Position = UDim2.fromOffset(216, 284); info.Size = UDim2.fromOffset(434, 52)
		info.TextWrapped = true; info.TextYAlignment = Enum.TextYAlignment.Top
		local function drawNow()
			local q = one()
			if q and q.Parent then
				local x = tonumber(q:GetAttribute("Xp")) or 0
				now.Text = ("%s: LV %d, %s XP"):format(string.upper(q.DisplayName), Ranks.levelOf(x), commas(x))
			else
				now.Text = "everyone: each goes up from their own level"
			end
			if wid then
				local e = Roster.byId[wid]
				local base = string.upper(if e then e.name else wid)
				if q and q.Parent then
					local mx = Mastery.xpOf(q, wid)
					wName.Text = ("%s  ·  %s: MASTERY %d (%s XP)"):format(base, string.upper(q.DisplayName), Mastery.levelOf(mx), commas(mx))
				else
					wName.Text = base
				end
			end
		end
		for i, id in Mastery.weapons() do
			local e = Roster.byId[id]
			local b = button(wl, "W_" .. id, string.upper(if e then e.name else id), UDim2.new(), 176, 26)
			b.LayoutOrder = i
			b.TextXAlignment = Enum.TextXAlignment.Left
			b.TextSize = 12
			T.new("UIPadding", { PaddingLeft = UDim.new(0, 8) }, b)
			wBtn[id] = b
			b.Activated:Connect(function()
				wid = id
				for k, bb in wBtn do lit(bb, k == id) end
				drawNow()
			end)
		end
		local function wname(): string
			local e = wid and Roster.byId[wid]
			return if e then e.name else tostring(wid)
		end
		giveMx.Activated:Connect(function()
			local n = numOf(mxBox)
			if not wid then note.Text = "pick a weapon first"; return end
			if not n then note.Text = "type how much mastery XP"; return end
			give("mastery", wid, n, ("%s %s mastery XP"):format(commas(n), wname()))
		end)
		setMl.Activated:Connect(function()
			local n = numOf(mlBox)
			if not wid then note.Text = "pick a weapon first"; return end
			if not n or n < 2 or n > Mastery.MAX then note.Text = ("type a mastery level, 2 to %d"):format(Mastery.MAX); return end
			give("masterylevel", wid, n, ("%s mastery %d"):format(wname(), n))
		end)
		table.insert(onTo, drawNow)
		Gift.xp = drawNow
	end

	-- UNLOCKS: any weapon with a lock (the 4 premium ones, and every one that opens at a level), or all of them. for
	-- good, like an early coin unlock
	do
		local P = kindPage.UNLOCKS
		local all = button(P, "UnlockAll", "UNLOCK ALL WEAPONS", UDim2.fromOffset(0, 0), 220, 34)
		lit(all, true)
		local ids = {}
		for _, e in Roster.list do
			if e.live and (Unlocks.robux(e.id) or Unlocks.level(e.id) > 1) then table.insert(ids, e.id) end
		end
		local info = T.text(P, "Info", ("Every locked weapon (%d: the premium ones and every one that opens at a level), for good. Never takes anything away."):format(#ids), 11, T.DIM, T.FONT, Enum.TextXAlignment.Left)
		info.Position = UDim2.fromOffset(232, 0); info.Size = UDim2.fromOffset(418, 34)
		info.TextWrapped = true
		all.Activated:Connect(function() give("unlockall", nil, nil, "every weapon") end)
		label(P, "OneHead", "ONE WEAPON", 0, 48, 200)
		local L = list(P, "List", UDim2.fromOffset(0, 68), UDim2.fromOffset(KW, 270))
		local rows: { [string]: TextLabel } = {}
		table.sort(ids, function(a, b)
			local ra, rb = Unlocks.robux(a), Unlocks.robux(b)
			if ra ~= rb then return ra end
			local la, lb = Unlocks.level(a), Unlocks.level(b)
			if la ~= lb then return la < lb end
			return a < b
		end)
		for i, id in ids do
			local e = Roster.byId[id]
			local row = T.new("Frame", { Name = "U_" .. id, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 28), LayoutOrder = i }, L)
			T.corner(row, 4)
			local t = T.text(row, "Name", string.upper(e.name), 12, T.TEXT, T.FONT_BOLD)
			t.Position = UDim2.fromOffset(8, 0); t.Size = UDim2.new(1, -330, 1, 0); t.TextTruncate = Enum.TextTruncate.AtEnd
			local k = T.text(row, "Lock", if Unlocks.robux(id) then "PREMIUM" else ("LEVEL %d"):format(Unlocks.level(id)), 11, if Unlocks.robux(id) then T.ACCENT else T.MUTED, T.FONT_BOLD)
			k.Position = UDim2.new(1, -320, 0, 0); k.Size = UDim2.fromOffset(90, 28)
			local has = T.text(row, "Has", "", 11, T.DIM, T.FONT_BOLD)
			has.Position = UDim2.new(1, -224, 0, 0); has.Size = UDim2.fromOffset(140, 28)
			rows[id] = has
			local g = button(row, "Give", "UNLOCK", UDim2.new(1, -78, 0, 2), 70, 24)
			g.TextSize = 11
			g.Activated:Connect(function() give("unlock", id, 1, e.name) end)
		end
		local function drawHas()
			local q = one()
			for id, l in rows do
				if q and q.Parent then
					local ok = Unlocks.forPlayer(q, id)
					l.Text = if ok and q:GetAttribute("UnlockAll") == true then "OPEN (DEV UNLOCK)" elseif ok then "THEY HAVE IT" else "LOCKED FOR THEM"
				else
					l.Text = ""
				end
			end
		end
		table.insert(onTo, drawHas)
		Gift.unlocks = drawHas
	end

	-- ANNOUNCE (19 Nov, round 4: "write announcements that go across the screen across all servers"): the text, then
	-- this server or every server (a second press). the server has Roblox's filter check it before anyone sees it
	-- (OwnerDev.server); everyone gets the banner (AnnounceBanner.client) and a chat line
	local apage = T.new("Frame", { Name = "Announce", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 60), Size = UDim2.new(1, 0, 1, -96), Visible = false }, plate)
	do
		local MAXA = 120
		label(apage, "AHead", ("ANNOUNCEMENT (UP TO %d LETTERS)"):format(MAXA), 18, 0, 400)
		local cnt = T.text(apage, "Count", "0 / " .. MAXA, 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
		cnt.Position = UDim2.fromOffset(782, 0); cnt.Size = UDim2.fromOffset(100, 16)
		local tb = box(apage, "Text", "", UDim2.fromOffset(18, 22), 864, "type the announcement here")
		tb.Size = UDim2.fromOffset(864, 64)
		tb.TextWrapped = true
		tb.TextXAlignment = Enum.TextXAlignment.Left
		tb.TextYAlignment = Enum.TextYAlignment.Top
		tb.TextSize = 16
		T.new("UIPadding", { PaddingLeft = UDim.new(0, 10), PaddingRight = UDim.new(0, 10), PaddingTop = UDim.new(0, 8) }, tb)
		tb:GetPropertyChangedSignal("Text"):Connect(function()
			local n = utf8.len(tb.Text) or #tb.Text
			if n > MAXA then
				local cut = utf8.offset(tb.Text, MAXA + 1)
				tb.Text = string.sub(tb.Text, 1, (cut or (MAXA + 1)) - 1)
				return
			end
			cnt.Text = ("%d / %d"):format(n, MAXA)
		end)
		local here = button(apage, "SendHere", "SEND TO THIS SERVER", UDim2.fromOffset(18, 100), 220, 34)
		local every = button(apage, "SendAll", "SEND TO ALL SERVERS", UDim2.fromOffset(246, 100), 220, 34)
		lit(here, true)
		local info = T.text(apage, "Info", ("Roblox's filter checks it before anyone sees it; if the filter doesn't answer, nothing is sent. Everyone gets a banner across the screen for about 6 s and a line in the chat. One every %d s."):format(10), 12, T.DIM, T.FONT, Enum.TextXAlignment.Left)
		info.Position = UDim2.fromOffset(18, 146); info.Size = UDim2.fromOffset(864, 40)
		info.TextWrapped = true; info.TextYAlignment = Enum.TextYAlignment.Top
		local armedAt = -math.huge
		local function send(scope: string)
			if tb.Text == "" then note.Text = "type the announcement first"; return end
			if scope == "all" and os.clock() - armedAt > 5 then
				armedAt = os.clock()
				note.Text = "ALL SERVERS: press SEND TO ALL SERVERS again to send it"
				return
			end
			armedAt = -math.huge
			note.Text = "the filter is checking it..."
			local r = call("announce", tb.Text, scope)
			if type(r) == "table" and r.ok then
				note.Text = tostring(r.did or "sent")
				tb.Text = ""
			else
				note.Text = "not sent: " .. tostring(if type(r) == "table" and r.why then r.why else "no answer")
			end
		end
		here.Activated:Connect(function() send("server") end)
		every.Activated:Connect(function() send("all") end)
	end

	-- FRIENDS (19 Nov: "allow me to temp give command panel to friends exclude the gifting portion of it"): lend the
	-- POWERS tab to a player here for 15 min, 30 min, 1 h or until they leave; REVOKE one, or REVOKE ALL. the server
	-- holds it (this server only, never saved) and refuses a friend anything but the powers (OwnerDev.server, TEMP DEV)
	local fpage = T.new("Frame", { Name = "Friends", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 60), Size = UDim2.new(1, 0, 1, -96), Visible = false }, plate)
	do
		label(fpage, "FHead", "LEND THE POWERS TAB (NEVER GIFT, XP, UNLOCKS, ANNOUNCE OR THE ANTI-CHEAT PANEL)", 18, 0, 700)
		local fl = list(fpage, "List", UDim2.fromOffset(18, 20), UDim2.fromOffset(864, 300))
		local revokeAll = button(fpage, "RevokeAll", "REVOKE ALL", UDim2.fromOffset(18, 330), 140, 30)
		local info = T.text(fpage, "Info", "This server only, never saved: it ends at its time, when they leave, or when the server closes. They can't do anything to you or another friend with dev. A match they use a power in counts for nothing, and every command they use goes in the anti-cheat panel's log.", 11, T.DIM, T.FONT, Enum.TextXAlignment.Left)
		info.Position = UDim2.fromOffset(170, 330); info.Size = UDim2.fromOffset(712, 44)
		info.TextWrapped = true; info.TextYAlignment = Enum.TextYAlignment.Top
		local function drawF()
			local res = call("players")
			clear(fl)
			if type(res) ~= "table" or not res.ok or type(res.players) ~= "table" then return end
			local n = 0
			for _, r in res.players do
				if typeof(r.ref) ~= "Instance" or not (r.ref :: Instance):IsA("Player") then continue end -- (dummies)
				n += 1
				local q = r.ref :: Player
				local row = T.new("Frame", { Name = "F_" .. tostring(r.user), BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 30), LayoutOrder = n }, fl)
				T.corner(row, 4)
				local nm = T.text(row, "Name", string.upper(tostring(r.name)), 12, T.TEXT, T.FONT_BOLD)
				nm.Position = UDim2.fromOffset(8, 0); nm.Size = UDim2.fromOffset(150, 30); nm.TextTruncate = Enum.TextTruncate.AtEnd
				local e = r.temp
				local st = T.text(row, "State", if e == 0 then "DEV UNTIL THEY LEAVE" elseif type(e) == "number" then "DEV UNTIL " .. os.date("%H:%M", e) else "", 11,
					T.ACCENT, T.FONT_BOLD)
				st.Position = UDim2.fromOffset(162, 0); st.Size = UDim2.fromOffset(170, 30)
				local x = 336
				local function act(name: string, text: string, w: number, fn: () -> ())
					local b = button(row, name, text, UDim2.fromOffset(x, 3), w, 24)
					b.TextSize = 11
					x += w + 4
					b.Activated:Connect(function() fn(); task.delay(0.15, drawF) end)
				end
				for _, m in { { 15, "15 MIN" }, { 30, "30 MIN" }, { 60, "1 HOUR" }, { 0, "UNTIL THEY LEAVE" } } do
					act("Lend" .. m[1], m[2], if m[1] == 0 then 120 else 56, function() said(call("grant", q, m[1]), "lent") end)
				end
				if e ~= nil then act("Revoke", "REVOKE", 64, function() said(call("revoke", q), "revoked") end) end
			end
			if n == 0 then
				local row = T.new("Frame", { Name = "Empty", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 28) }, fl)
				local t = T.text(row, "Text", "nobody else here", 12, T.DIM)
				t.Position = UDim2.fromOffset(8, 0); t.Size = UDim2.new(1, -16, 1, 0)
			end
		end
		revokeAll.Activated:Connect(function() said(call("revokeAll"), "revoked"); task.delay(0.15, drawF) end)
		Gift.friends = drawF
		Gift.friendsOn = function() return fpage.Visible end
	end

	local kind = "CONTAINERS"
	local function showKind(k: string)
		kind = k
		for name, b in kindBtn do lit(b, name == k) end
		for name, f in kindPage do f.Visible = name == k end
		if k == "ITEMS" and Gift.items then Gift.items() end
		if k == "XP" and Gift.xp then Gift.xp() end
		if k == "UNLOCKS" and Gift.unlocks then Gift.unlocks() end
	end
	for name, b in kindBtn do b.Activated:Connect(function() showKind(name) end) end
	-- which: "powers", "gift", "announce" (true / false: gift / powers, as before)
	local function showTab(which: any)
		local w = if which == true then "gift" elseif which == false then "powers" else tostring(which)
		if not OWNER then w = "powers" end -- (TEMP DEV: the powers only)
		Gift.shown = w == "gift"
		page.Visible = w == "gift"
		apage.Visible = w == "announce"
		fpage.Visible = w == "friends"
		for _, c in powersKids do c.Visible = w == "powers" end
		lit(tabPowers, w == "powers")
		lit(tabGift, w == "gift")
		lit(tabAnnounce, w == "announce")
		lit(tabFriends, w == "friends")
		if w == "gift" then drawTo(); showKind(kind) end
		if w == "friends" then task.spawn(Gift.friends) end
	end
	tabPowers.Activated:Connect(function() showTab("powers") end)
	tabGift.Activated:Connect(function() showTab("gift") end)
	tabAnnounce.Activated:Connect(function() showTab("announce") end)
	tabFriends.Activated:Connect(function() showTab("friends") end)
	showTab("powers")
	Gift.refresh = function() if Gift.shown then drawTo() end end
	Gift.showTab = showTab
	Players.PlayerAdded:Connect(function() Gift.refresh() end)
	Players.PlayerRemoving:Connect(function() task.defer(Gift.refresh) end)
end

local function setOpen(on: boolean)
	if open == on then return end
	open = on
	gui.Enabled = on
	MenuCursor.set("dev", on, function() return gui.Enabled end, true) -- (the mouse, but you can still move: try a fly with it up)
	if on then
		drawMe()
		refreshPlayers()
	end
end
local function toggle() if lent() or open then setOpen(not open) end end
close.Activated:Connect(function() setOpen(false) end)
gui:GetPropertyChangedSignal("Enabled"):Connect(function() if not gui.Enabled and open then setOpen(false) end end)
task.spawn(function()
	while true do
		task.wait(2)
		if open then refreshPlayers() end
		if open and Gift.friendsOn and Gift.friendsOn() then Gift.friends() end
	end
end)

-- a pad: B backs out of it, VIEW reaches the DEV button (PadNav's Pad.MENUS, once PadNav has put it there)
task.spawn(function()
	local pm = J:FindFirstChild("Pad")
	local ok, Pad = false, nil
	if pm and pm:IsA("ModuleScript") then ok, Pad = pcall(require, pm) end
	if not ok or type(Pad) ~= "table" then return end
	for _ = 1, 60 do
		if type((Pad :: any).MENUS) == "table" then
			(Pad :: any).MENUS.dev = { gui = "OwnerDev", back = function() setOpen(false) end }
			return
		end
		task.wait(1)
	end
end)

-- the DEV button: a small one in the corner, the owner's only (touch, and a pad through VIEW; a mouse can click it too)
do
	local bg = T.new("ScreenGui", { Name = "JankDevButton", ResetOnSpawn = false, DisplayOrder = 5, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	local b = T.new("TextButton", {
		Name = "Dev", Text = "DEV", FontFace = T.FONT_BOLD, TextSize = 12, AutoButtonColor = true, TextColor3 = T.ACCENT,
		BackgroundColor3 = T.BG, BackgroundTransparency = 0.3, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 104), Size = UDim2.fromOffset(46, 24), -- (under the currency box)
	}, bg)
	T.corner(b, 4)
	T.edge(b, T.ACCENT, 0.6)
	b.Activated:Connect(toggle)
	local chip = T.new("TextLabel", {
		Name = "DevKeys", Text = "DEV KEYS ON", FontFace = T.FONT_BOLD, TextSize = 10, TextColor3 = T.INK,
		BackgroundColor3 = T.ACCENT, BackgroundTransparency = 0.05, BorderSizePixel = 0, Visible = false,
		AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 132), Size = UDim2.fromOffset(74, 16),
	}, bg)
	T.corner(chip, 3)
	keysChip = chip
	drawAim()
	-- (TEMP DEV: the button goes, the menu shuts and the aim keys go off the moment the owner's loan ends; back if lent again)
	local function lentNow()
		bg.Enabled = lent()
		if not lent() then
			setOpen(false)
			if aimKeys then aimKeys = false; drawAim() end
		end
	end
	me:GetAttributeChangedSignal("DevTemp"):Connect(lentNow)
	lentNow()
end

-- F8, "/dev", X and Z
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "JankDev"
	cmd.PrimaryAlias = "/dev"
	cmd.Parent = TextChatService
	cmd.Triggered:Connect(function() toggle() end)
end
me:GetAttributeChangedSignal("DevPanel"):Connect(toggle)
local function lookDir(): Vector3?
	local cam = workspace.CurrentCamera
	return if cam then cam.CFrame.LookVector else nil
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or typing() or not lent() then return end
	if io.KeyCode == Enum.KeyCode.F8 then
		toggle()
	elseif aimKeys and (io.KeyCode == Enum.KeyCode.X or io.KeyCode == Enum.KeyCode.Z or io.KeyCode == Enum.KeyCode.Y) then
		local lk = lookDir()
		if not lk then return end
		local res = call(if io.KeyCode == Enum.KeyCode.X then "flingAim" elseif io.KeyCode == Enum.KeyCode.Z then "freezeAim" else "redcardAim", lk)
		if open then said(res, "done"); task.delay(0.2, refreshPlayers) end
	end
end)

-- (Studio tests: player attribute DevMenuTest = "open" / "close")
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("DevMenuTest"):Connect(function()
		local v = me:GetAttribute("DevMenuTest")
		if v == "open" then setOpen(true) elseif v == "close" then setOpen(false)
		elseif v == "gift" then setOpen(true); Gift.showTab("gift")
		elseif v == "announce" then setOpen(true); Gift.showTab("announce")
		elseif v == "friends" then setOpen(true); Gift.showTab("friends")
		elseif v == "keys" then aimKeys = not aimKeys; drawAim() end
	end)
end
