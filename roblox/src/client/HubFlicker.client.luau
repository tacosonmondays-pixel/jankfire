--!strict
-- HubFlicker (20 Nov 2026): the hubs' zombies rooms (HubKit.zombieRoom) have a dying bulb. Parts tagged HubFlicker (a
-- Neon bulb with a light in it) stutter out now and then while the camera is within NEAR studs: two or three drops of
-- 0.04-0.12 s every 1.5-6 s. Writes happen only on a change, a few a second at most, never per frame
-- (roblox/docs/PERFORMANCE.md); a culled or removed bulb's loop ends and starts again when it comes back.
local CollectionService = game:GetService("CollectionService")

local NEAR = 90
local OFF_COL = Color3.fromHex("5a554c")
local running: { [BasePart]: boolean } = {}

local function run(p: BasePart)
	if running[p] then return end
	running[p] = true
	local light = p:FindFirstChildWhichIsA("Light")
	local onCol, onMat = p.Color, p.Material
	local bright = if light then light.Brightness else 0
	local function set(on: boolean)
		p.Material = if on then onMat else Enum.Material.SmoothPlastic
		p.Color = if on then onCol else OFF_COL
		if light then light.Brightness = if on then bright else bright * 0.08 end
	end
	task.spawn(function()
		while p:IsDescendantOf(workspace) do
			task.wait(1.5 + math.random() * 4.5)
			local cam = workspace.CurrentCamera
			if cam and p:IsDescendantOf(workspace) and (cam.CFrame.Position - p.Position).Magnitude < NEAR then
				for _ = 1, math.random(2, 3) do
					set(false); task.wait(0.04 + math.random() * 0.08)
					set(true); task.wait(0.05 + math.random() * 0.12)
				end
			end
		end
		set(true)
		running[p] = nil
	end)
end

for _, p in CollectionService:GetTagged("HubFlicker") do if p:IsA("BasePart") then run(p) end end
CollectionService:GetInstanceAddedSignal("HubFlicker"):Connect(function(p) if p:IsA("BasePart") then run(p) end end)
