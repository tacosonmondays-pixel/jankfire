--!strict
-- THE HUB'S CONSOLE (20 Nov 2026; the centre redone, HubRotundaRing): the round console in the middle of the hall shows on
-- its rim how many players wait for each mode on THIS server: those standing on the pads (Matches.padView(), both banks
-- of each mode) and those searching through the PLAY button (Queue's entries still searching, casual and ranked; an entry
-- whose match was just found is out of it). With cross-server on a PLAY search also searches here, so these are this
-- server's waiting players, which is what "N WAITING" on a hub console means. Written once a second onto every label
-- tagged HubConsoleRim (attribute Mode = the mode's id: the builder's rim panels), its Gui's second line. Nothing to do
-- while the hub has no console (the layouts before the ring).
-- (play-party-ranked, 20 Nov: padView and Queue.entries are the sources; require them here, one shared copy.)
local CollectionService = game:GetService("CollectionService")

local Matches = require(script.Parent:WaitForChild("Matches")) :: any
local Queue = require(script.Parent:WaitForChild("Queue")) :: any

local TAG = "HubConsoleRim"

local function counts(): { [string]: number }
	local out: { [string]: number } = {}
	local ok, view = pcall(Matches.padView)
	if ok and type(view) == "table" then
		for pad, v in view do
			local mode = if typeof(pad) == "Instance" then pad:GetAttribute("Mode") else nil
			if type(mode) == "string" and type(v) == "table" and type(v.sides) == "table" then
				local n = 0
				for _, side in v.sides do if type(side) == "table" then n += #side end end
				out[mode] = (out[mode] or 0) + n
			end
		end
	end
	for _, rim in CollectionService:GetTagged(TAG) do
		local mode = rim:GetAttribute("Mode")
		if type(mode) == "string" and out[mode] == nil then out[mode] = 0 end
	end
	for mode in out do
		for _, ranked in { false, true } do
			local ok2, es = pcall(Queue.entries, Queue.key(mode, ranked))
			if ok2 and type(es) == "table" then
				for _, e in es do
					if type(e) == "table" and e.state == "search" and type(e.size) == "number" then out[mode] += e.size end
				end
			end
		end
	end
	return out
end

local shown: { [Instance]: string } = {}
task.spawn(function()
	while true do
		local rims = CollectionService:GetTagged(TAG)
		if #rims > 0 then
			local c = counts()
			for _, rim in rims do
				local mode = rim:GetAttribute("Mode")
				local gui = rim:FindFirstChildWhichIsA("SurfaceGui")
				local line = gui and gui:FindFirstChild("Line2")
				if type(mode) == "string" and line and line:IsA("TextLabel") then
					local text = ("%d WAITING"):format(c[mode] or 0)
					if shown[rim] ~= text then shown[rim] = text; line.Text = text end
				end
			end
		end
		task.wait(1)
	end
end)
