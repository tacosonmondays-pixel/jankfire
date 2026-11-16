--!strict
-- a way for a Studio play test to reach the running server. the Studio MCP's own Luau runs beside the game with its
-- own copies of the modules, so it can't see the fighters; this gives it a BindableFunction, ServerStorage.JankTest,
-- that ONLY exists in Studio (nothing here runs in a live server, and a client can never call a BindableFunction).
-- a test can arm itself with any weapons WITHOUT touching the saved loadout, and read the server's own numbers (HP,
-- ammo, the Yeehaw's chain) to check them against the spec.
--   local T = game.ServerStorage.JankTest
--   T:Invoke("arm", player, { "smg", "revolver", "katana" })   -> true (this life only, not saved; nothing owned needed)
--   T:Invoke("arm", player, { "ar@<skin>", "revolver", "katana", "frag" })   (a skin on a gun, the item on G)
--     -> false, "why" when it can't
--   T:Invoke("me", player)    -> { hp, alive, held, ammo = { smg = 45 }, chain, aiming, kills }
--   T:Invoke("all")           -> { { name, kind, hp, alive, pos } ... }
--   T:Invoke("hp", "Dummy", 100)  -> sets a fighter's HP by name (a dummy that must survive a volley)
--   T:Invoke("item", player, "frag") -> gives this life that item with full charges (nil: just read) and returns the
--     server's numbers: { item, n, next, heal, hp, projs, bubbles, clouds }
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("Jankfire")
local GunSkins = require(Shared:WaitForChild("GunSkins"))
local Items = require(Shared:WaitForChild("Items"))

local TestHook = {}

function TestHook.init(Fight: any, Rules: any, Weapons: any)
	if not RunService:IsStudio() then return end
	local old = ServerStorage:FindFirstChild("JankTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankTest"
	fn.OnInvoke = function(op: any, a: any, b: any, c: any): any
		if op == "arm" then
			-- (Studio only: nothing owned is asked for) b = the weapons: { primary, secondary, melee } ids, each may be
			-- "<weapon>@<skin>", a 4th entry is the item on G; or { primary =, secondary =, melee =, utility =,
			-- skins = { [weapon] = skin } }. waits up to 5 s for a player who hasn't spawned yet. true, or false and why
			local t0 = os.clock()
			local f = Fight.byPlayer[a]
			while not f and typeof(a) == "Instance" and a:IsA("Player") and os.clock() - t0 < 5 do task.wait(0.1); f = Fight.byPlayer[a] end
			if not f then return false, "that player isn't a fighter (not spawned?)" end
			if type(b) ~= "table" then return false, "weapons: { primary, secondary, melee }" end
			local list, skins, item = {}, {}, nil
			if b[1] ~= nil then
				for i, v in b do
					if type(v) ~= "string" then return false, "entry " .. tostring(i) .. " isn't an id" end
					if i == 4 then item = v; continue end
					local wid, skin = string.match(v, "^([%w_]+)@([%w_]+)$")
					table.insert(list, wid or v)
					if wid then skins[wid] = skin end
				end
			else
				list = { b.primary, b.secondary, b.melee }
				item = b.utility
				if type(b.skins) == "table" then for w, sk in b.skins do skins[w] = sk end end
			end
			if #list ~= 3 then return false, ("3 weapons (primary, secondary, melee), not %d"):format(#list) end
			for _, id in list do if type(id) ~= "string" or not Weapons.list[id] then return false, "not a weapon: " .. tostring(id) end end
			for w, sk in skins do if sk ~= "default" and not GunSkins.valid(w, sk) then return false, ("no skin %s for %s here"):format(tostring(sk), w) end end
			if item ~= nil and (type(item) ~= "string" or not Items.list[item]) then return false, "not an item: " .. tostring(item) end
			-- the skins go on the player's Skins attribute (the one Loadout publishes, "weapon=skin;..."), others kept
			if next(skins) then
				local have = {}
				local cur = a:GetAttribute("Skins")
				if type(cur) == "string" then for w, sk in string.gmatch(cur, "([%w_]+)=([%w_]+)") do have[w] = sk end end
				for w, sk in skins do have[w] = if sk == "default" then nil else sk end
				local parts = {}
				for w, sk in have do table.insert(parts, w .. "=" .. sk) end
				a:SetAttribute("Skins", table.concat(parts, ";"))
			end
			f.nextLoadout = list
			Rules.arm(f, os.clock())
			Fight.showWeapon(f)
			a:SetAttribute("Loadout", table.concat(list, ","))
			a:SetAttribute("ArmT", (tonumber(a:GetAttribute("ArmT")) or 0) + 1)
			if item then require(script.Parent:WaitForChild("Utility")).test(f, item) end
			return true
		elseif op == "me" then
			local f = Fight.byPlayer[a]
			if not f then return nil end
			local ammo = {}
			for id, am in f.ammo do ammo[id] = am.mag end
			return { hp = f.hp, alive = f.alive, held = f.held, ammo = ammo, chain = if f.lev then f.lev.k else 0, aiming = f.aimT ~= nil, kills = f.kills }
		elseif op == "all" then
			local out = {}
			for _, f in Fight.all do
				local r = Fight.root(f)
				table.insert(out, { name = f.name, kind = f.kind, hp = f.hp, alive = f.alive, pos = if r then r.Position else nil })
			end
			return out
		elseif op == "item" then
			local f = Fight.byPlayer[a]
			if not f then return nil end
			return require(script.Parent:WaitForChild("Utility")).test(f, if type(b) == "string" then b else nil)
		elseif op == "smoke" then -- (a, b: two points) does a smoke cloud stand between them
			return Fight.smokeBlocks(a, b)
		elseif op == "rev" then -- (a fighter's name or model, secs) a reverse card on them: Utility.testReverse
			for _, f in Fight.all do
				if (f.name == a or Fight.model(f) == a) and f.alive then require(script.Parent:WaitForChild("Utility")).testReverse(f, if type(b) == "number" then b else 3); return true end
			end
			return false
		elseif op == "hurt" then -- (a fighter's name or model, amount, by: a player) one hit through Fight.hurt; their HP after
			for _, f in Fight.all do
				if (f.name == a or Fight.model(f) == a) and f.alive and type(b) == "number" then
					Fight.hurt(f, b, if typeof(c) == "Instance" then Fight.byPlayer[c] else nil, "test", false)
					return f.hp
				end
			end
			return nil
		elseif op == "hp" then
			for _, f in Fight.all do
				if f.name == a and f.alive and type(b) == "number" then f.hp = b; Fight.syncHp(f); return true end
			end
			return false
		end
		return nil
	end
	fn.Parent = ServerStorage
end

return TestHook
