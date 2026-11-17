--!strict
-- the hub's VIP door (HubRotundaRooms builds it, behind the lounge): its looks on your own screen. who may pass is the
-- server's decision (HubVip.server: Vip.isVip, a collision group that lets a VIP's character through the leaves, and a
-- check that puts anyone else back out of the room); the player attribute VIP it sets is only for looks:
--   a VIP: the door's leaves (Models tagged VipDoor, each with Slide = how far it moves to open) slide open as you come
--   near, and the "Get VIP" prompt is off
--   anyone else: the door stays shut and silent, and its prompt (on the part tagged VipPrompt, ShopOpen = "vip") opens
--   the shop on the VIP tile (ShopClient acts on that)
-- its sounds (17 Nov 2026, the owner: "the door to the vip can you make a sliding door sound with the bell happening
-- before it opens? make it to it cant be spammed!", then: "when the vip doors open after they open ding, I think thats a
-- good spot"): the leaves slide open at once with a sliding-door sound, the chime dings as they finish opening, and a
-- softer slide (no chime) plays as they close. Sounds door_vip_slide / door_vip_bell in JankfireSounds (recordings,
-- roblox/docs/SOUNDS.md). no spam: each door (the leaves sharing a parent) is one state,
--   closed -> opening -> open -> closing -> closed
-- it opens when you come within OPEN_R, stays open while you're within CLOSE_R (a wider ring, so walking along the edge
-- can't flap it) and for at least MIN_OPEN, dings once per opening and never twice within BELL_GAP (a reopening inside
-- that just slides). a reversal midway carries on from where the leaves are. the zone stings stay quiet across this
-- door (ZoneSounds): these are its only sounds. while ZoneCull has the hub out of your world the state is kept; when it
-- comes back it is set straight to where it should be, with no sound (as the training shutters, 5a87449)
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local Sfx = require(script.Parent:WaitForChild("Sfx"))

local me = Players.LocalPlayer
local OPEN_R, CLOSE_R = 10, 14 -- (studs from the door: opens inside OPEN_R, closes only once you're past CLOSE_R)
local SPEED = 3.2 -- (opening takes about a third of a second)
local MIN_OPEN = 2 -- (seconds it stays open at least, counted from when it starts to open)
local BELL_GAP = 5 -- (seconds: no second chime inside this, even if it closes and reopens)

type Leaf = { m: Model, parts: { { p: BasePart, home: CFrame } }, slide: Vector3 }
type Door = { leaves: { Leaf }, center: Vector3, state: string, t: number, since: number, lastBell: number, rung: boolean, shown: boolean }
local doors: { [Instance]: Door } = {}
local leafOf: { [Model]: Door } = {}

local function centre(d: Door)
	local sum, n = Vector3.zero, 0
	for _, lf in d.leaves do for _, q in lf.parts do sum += q.home.Position; n += 1 end end
	if n > 0 then d.center = sum / n end
end

local function addLeaf(m: Instance)
	if not m:IsA("Model") or leafOf[m] then return end
	local slide = m:GetAttribute("Slide")
	if typeof(slide) ~= "Vector3" then return end
	local lf: Leaf = { m = m, parts = {}, slide = slide }
	for _, p in m:GetDescendants() do if p:IsA("BasePart") then table.insert(lf.parts, { p = p, home = p.CFrame }) end end
	if #lf.parts == 0 then return end
	local key = m.Parent or m
	local d = doors[key]
	if not d then
		d = { leaves = {}, center = Vector3.zero, state = "closed", t = 0, since = -math.huge, lastBell = -math.huge, rung = false, shown = true }
		doors[key] = d
	end
	table.insert(d.leaves, lf)
	leafOf[m] = d
	centre(d)
end
local function removeLeaf(m: Instance)
	local d = leafOf[m :: Model]
	if not d then return end
	leafOf[m :: Model] = nil
	for i, lf in d.leaves do if lf.m == m then table.remove(d.leaves, i); break end end
	centre(d)
end
CollectionService:GetInstanceAddedSignal("VipDoor"):Connect(addLeaf)
CollectionService:GetInstanceRemovedSignal("VipDoor"):Connect(removeLeaf)
for _, m in CollectionService:GetTagged("VipDoor") do addLeaf(m) end

local function isVip(): boolean return me:GetAttribute("VIP") == true end

local function prompts()
	local vip = isVip()
	for _, p in CollectionService:GetTagged("VipPrompt") do
		local pr = p:FindFirstChildWhichIsA("ProximityPrompt")
		if pr then pr.Enabled = not vip end
	end
end
me:GetAttributeChangedSignal("VIP"):Connect(prompts)
CollectionService:GetInstanceAddedSignal("VipPrompt"):Connect(prompts)
prompts()

local function place(d: Door)
	local e = d.t * d.t * (3 - 2 * d.t)
	for _, lf in d.leaves do for _, q in lf.parts do q.p.CFrame = q.home + lf.slide * e end end
end

-- from shut (or closing) toward open: the slide now, the chime when it's fully open (once, gap allowing)
local function startOpening(d: Door, now: number)
	d.since = now
	d.rung = false
	Sfx.play("door_vip_slide", d.center)
	d.state = "opening"
end

RunService.RenderStepped:Connect(function(dt: number)
	if next(doors) == nil then return end
	local now = os.clock()
	local vip = isVip()
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	for _, d in doors do
		if #d.leaves == 0 then continue end
		local dist = if vip and root then (root.Position - d.center).Magnitude else math.huge
		if not d.leaves[1].m:IsDescendantOf(workspace) then d.shown = false; continue end -- (ZoneCull: keep the state)
		if not d.shown then
			-- (back in your world: straight to where it should be, no replay and no sound)
			d.shown = true
			local open = dist < CLOSE_R and (d.state ~= "closed" or dist < OPEN_R)
			d.state, d.t = if open then "open" else "closed", if open then 1 else 0
			d.rung = true
			if open then d.since = now end
			place(d)
			continue
		end
		local st = d.state
		if st == "closed" then
			if dist < OPEN_R then startOpening(d, now) end
		elseif st == "opening" or st == "open" then
			if dist >= CLOSE_R and now - d.since >= MIN_OPEN then
				Sfx.play("door_vip_slide", d.center, 0.55, 0.94)
				d.state = "closing"
			end
		elseif st == "closing" then
			if dist < OPEN_R then startOpening(d, now) end -- (back before it shut: open again from where it is)
		end
		local goal = if d.state == "opening" or d.state == "open" then 1 else 0
		if d.t ~= goal then
			d.t = math.clamp(d.t + (if goal > d.t then dt else -dt) * SPEED, 0, 1)
			place(d)
		end
		if d.state == "opening" and d.t >= 1 then
			d.state = "open"
			if not d.rung and now - d.lastBell >= BELL_GAP then
				d.rung, d.lastBell = true, now
				Sfx.play("door_vip_bell", d.center)
			end
		end
		if d.state == "closing" and d.t <= 0 then d.state = "closed" end
	end
end)
