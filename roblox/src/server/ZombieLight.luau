--!strict
-- ZOMBIES lights (27 Nov 2026, the owner: "Can you make zombies having glowing eyes, also some parts of the map you need
-- a flashlight it'll be like most games f for flashlight?"). The server's side; each client's: ZombieLight.client.
--   * the eyes: two small Neon pieces on every zombie's face, put on the bodies every zombie is cloned from (so the
--     specials and the bosses too, scaled with them) and on the intro crowd's shambler. No light of their own: 36 at a
--     time would cost too much (a boss gets a faint one on each client)
--   * the flashlights: a player's on / off is the player attribute ZmLight (the client asks with { k = "light" } on the
--     Zm remote: F, D-pad up, the phone's LIGHT); a squad bot's is its body's ZmLight, on while it stands in a dark area
--     before the power. Every client draws every beam (ForestLife's pattern)
--   * the dark areas (ZM.DARK): the lamps in them wait for the power (tagged PowerLight: ZombieExtra turns those on
--     with it); each client dims its own light while its camera is in one
-- Installed after ZombieExtract (ZombiesServer); its hooks chain on.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))

local ZombieLight = {}

-- two small Neon eyes on a body's face, welded to its head (nothing queries or touches them: shots hit the rig)
function ZombieLight.eyes(m: Model)
	local head = m:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") or head:FindFirstChild("ZmEyeL") then return end
	local hs = head.Size
	for _, side in { -1, 1 } do
		local e = Instance.new("Part")
		e.Name = if side < 0 then "ZmEyeL" else "ZmEyeR"
		e.Material = Enum.Material.Neon
		e.Color = ZM.EYE
		e.Size = Vector3.new(hs.X * 0.22, hs.Y * 0.1, 0.06) -- (27 Nov Play check: a third smaller read as two faint dashes at 16 studs)
		e.CanCollide, e.CanQuery, e.CanTouch, e.Massless, e.CastShadow = false, false, false, true, false
		e.Anchored = false
		e.CollisionGroup = head.CollisionGroup
		e.CFrame = head.CFrame * CFrame.new(side * hs.X * 0.2, hs.Y * 0.08, -hs.Z * 0.47)
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = head, e
		w.Parent = e
		e.Parent = head
	end
end

function ZombieLight.install(Z: any)
	local ext, X = Z.ext, Z.X
	local Fight = X.fight()
	local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent

	local function chain(name: string, fn: (...any) -> any)
		local prev = ext[name]
		ext[name] = function(...)
			local r = if prev then prev(...) else nil
			local mine = fn(r, ...)
			if mine ~= nil then return mine end
			return r
		end
	end
	local function memberOf(g: any, p: Player): any
		for _, m in g.members do if m.p == p then return m end end
		return nil
	end

	chain("start", function(_r: any, g: any)
		-- the eyes: on the bodies every zombie is cloned from, and the intro's shambler (ZombieExtract copied it already)
		for _, t in g.templates or {} do ZombieLight.eyes(t) end
		local cine = ReplicatedStorage:FindFirstChild("JankfireZmCine")
		local zt = cine and cine:FindFirstChild("Zombie")
		if zt and zt:IsA("Model") then ZombieLight.eyes(zt) end
		-- the dark areas' lamps wait for the power
		local n = 0
		if g.map then
			for _, l in g.model:GetDescendants() do
				if l:IsA("Light") and not CollectionService:HasTag(l, "PowerLight") then
					local par = l.Parent
					local at = if par and par:IsA("BasePart") then par.Position elseif par and par:IsA("Attachment") then par.WorldPosition else nil
					local a = if at then ZM.areaAt(g.map, at) else nil
					if a and ZM.DARK[a] then
						CollectionService:AddTag(l, "PowerLight")
						l.Enabled = false
						n += 1
					end
				end
			end
		end
		g.model:SetAttribute("ZmDarkLamps", n)
		for _, m in g.members do if m.p then m.p:SetAttribute("ZmLight", false) end end
		return nil
	end)

	-- a player's flashlight: on or off (F; the client plays the click)
	local lastT: { [Player]: number } = {}
	zr.OnServerEvent:Connect(function(p: Player, msg: any)
		if type(msg) ~= "table" or msg.k ~= "light" then return end
		local g = Z.game()
		if not g or not memberOf(g, p) then return end
		local t = os.clock()
		if lastT[p] and t - lastT[p] < 0.15 then return end
		lastT[p] = t
		p:SetAttribute("ZmLight", p:GetAttribute("ZmLight") ~= true)
	end)
	Players.PlayerRemoving:Connect(function(p: Player) lastT[p] = nil end)

	-- the bots' flashlights (on in a dark area before the power), and nobody's once their game is over
	task.spawn(function()
		while true do
			task.wait(0.4)
			local g = Z.game()
			for _, p in Players:GetPlayers() do
				if p:GetAttribute("ZmLight") ~= nil and (not g or not memberOf(g, p)) then p:SetAttribute("ZmLight", nil) end
			end
			if g and g.map and g.model and g.model.Parent then
				local power = g.model:GetAttribute("Power") == true
				for _, m in g.members do
					if m.bot then
						local body = Fight.model(m.f)
						local root = body and body:FindFirstChild("HumanoidRootPart")
						local on = false
						if root and root:IsA("BasePart") and not power and m.f.alive and not m.down then
							local a = ZM.areaAt(g.map, root.Position)
							on = a ~= nil and ZM.DARK[a] == true
						end
						if body and body:GetAttribute("ZmLight") ~= on then body:SetAttribute("ZmLight", on) end
					end
				end
			end
		end
	end)
end

return ZombieLight
