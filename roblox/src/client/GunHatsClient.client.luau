-- the weapon hats on this client (GunHats.luau): their moving bits every frame (the propeller turns, the halo bobs,
-- the googly pupils rattle: on your gun, everyone's, the previews and the racks), your hats on the hub armory's
-- display guns (the boards show the weapons as you carry them: your pick's hat on each), and the hat models fetched
-- up front so a hat never comes out blank the first time
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local GunHats = require(Shared:WaitForChild("GunHats"))
local me = Players.LocalPlayer

RunService.RenderStepped:Connect(function(dt) GunHats.step(dt) end)

task.spawn(function()
	local lib = ReplicatedStorage:WaitForChild("JankfireHats", 15)
	if lib then pcall(function() game:GetService("ContentProvider"):PreloadAsync(lib:GetChildren()) end) end
end)

-- the armory's boards: every display gun named "Rack_w_<id>" (HubRotunda's B.gun) wears your hat for that weapon
local function racks()
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	if not hub then return 0 end
	local n = 0
	-- (a piece of the hub that ZoneCull has put aside on this client waits in ReplicatedStorage.ZoneCullHidden)
	local list = hub:GetDescendants()
	local aside = ReplicatedStorage:FindFirstChild("ZoneCullHidden")
	if aside then for _, d in aside:GetDescendants() do table.insert(list, d) end end
	for _, d in list do
		if d:IsA("Model") then
			local wid = string.match(d.Name, "^Rack_w_([%w_]+)$")
			if wid then
				if GunHats.attachDisplay(d, wid, GunHats.hatFor(me, wid)) then n += 1 end
			end
		end
	end
	return n
end
me:GetAttributeChangedSignal("Hats"):Connect(racks)
task.spawn(function()
	-- (the hub may still be arriving: try a few times)
	for _ = 1, 6 do
		if workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") then racks() end
		task.wait(2)
	end
end)
