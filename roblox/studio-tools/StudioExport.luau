-- edit-time: hands the place's scripts and models to the Roblox Studio MCP so they can be written into the git repo
-- (Studio can't write files, and its HTTP allowlist blocks localhost, so the data goes out as the call's return value;
-- the MCP saves a big result to a text file and tools/roblox/studio_export_unpack.mjs turns that file into real files).
-- from the MCP (execute_luau, Edit). every call must clone + require, because the module changes:
--   local m = game.ServerStorage.PolishBackup.StudioExport:Clone(); local E = require(m); m:Destroy()
--   return E.run("bundle")        -- packs every script + settings + model file into one ASCII string (kept in _G).
--                                    E.run("bundle", "src/") = only the code, E.run("bundle", "place/Lighting") = only that
--   return E.run("slice", n)      -- slice n of it (1..N). each slice is just under the MCP's 100,000 character cut
--   return E.run("done")          -- frees the memory
-- then: node tools/roblox/studio_export_unpack.mjs <the N result files>   (order doesn't matter)
-- not exported: ServerStorage backups (PreWeaponsBackup, PolishBackup's old copies such as HubV1 to HubV6 and its
-- Fx / Arsenal / Move script copies), Terrain's cells (the clouds are exported), the Camera
local Http = game:GetService("HttpService")
local Ser = game:GetService("SerializationService")
local Enc = game:GetService("EncodingService")
local RS, SSS, ST = game:GetService("ReplicatedStorage"), game:GetService("ServerScriptService"), game:GetService("ServerStorage")
local SPS = game:GetService("StarterPlayer").StarterPlayerScripts

local E = {}
local CHUNK = 96000 -- characters per slice (the MCP cuts a result at 100,000)

local function ext(d: Instance): string
	if d:IsA("LocalScript") then return ".client.luau" elseif d:IsA("Script") then return ".server.luau" end
	return ".luau"
end

-- where each script lives in the repo (Rojo names). the three Jankfire folders are the Rojo-synced code
local function scripts(): { { path: string, source: string } }
	local out = {}
	local function folder(root: Instance, dir: string)
		for _, d in root:GetChildren() do
			if d:IsA("LuaSourceContainer") then table.insert(out, { path = dir .. "/" .. d.Name .. ext(d), source = (d :: any).Source }) end
		end
	end
	folder(RS.Jankfire, "src/shared"); folder(SSS.Jankfire, "src/server"); folder(SPS.Jankfire, "src/client")
	folder(SSS, "src/server_root"); folder(SPS, "src/client_root") -- loose scripts next to the Jankfire folders
	-- scripts living inside models (they also travel inside the model's .rbxm; this copy is the readable one)
	for _, d in RS:GetDescendants() do
		if d:IsA("LuaSourceContainer") and not d:IsDescendantOf(RS.Jankfire) then
			table.insert(out, { path = "src/in_models/" .. d:GetFullName():gsub("%.", "/") .. ext(d), source = (d :: any).Source })
		end
	end
	-- the edit-time helpers worth keeping
	for _, n in { "PropPlacer", "OverlapCheck", "CozyKit", "Hub2Colors", "StudioExport", "HubLab", "HubRotunda", "HubRotundaCentre", "HubRotundaLifts", "HubRotundaRooms", "KitImport", "HubReskin", "WeaponImport", "WeaponPaint", "WeaponKit", "SeriousPass", "StructurePass", "RooftopV2", "RooftopV2Layout", "TrainingV2" } do
		local d = ST.PolishBackup:FindFirstChild(n)
		if d and d:IsA("LuaSourceContainer") then table.insert(out, { path = "studio-tools/" .. n .. ".luau", source = (d :: any).Source }) end
	end
	return out
end

local function plain(v: any): any
	local t = typeof(v)
	if t == "Color3" then return "#" .. v:ToHex() elseif t == "Vector3" then return { v.X, v.Y, v.Z } elseif t == "EnumItem" then return v.Name end
	if t == "number" or t == "boolean" or t == "string" then return v end
	return tostring(v)
end
local function props(inst: Instance, names: { string }): { [string]: any }
	local o = {}
	for _, n in names do local ok, v = pcall(function() return (inst :: any)[n] end); if ok then o[n] = plain(v) end end
	return o
end
-- the service properties a rebuild would need (the things that aren't instances)
local function settings(): string
	local L = game:GetService("Lighting")
	local s = {
		Lighting = props(L, { "Ambient", "OutdoorAmbient", "Brightness", "ClockTime", "GeographicLatitude", "ExposureCompensation", "EnvironmentDiffuseScale", "EnvironmentSpecularScale", "GlobalShadows", "ShadowSoftness", "ColorShift_Top", "ColorShift_Bottom", "FogStart", "FogEnd", "FogColor", "LightingStyle", "PrioritizeLightingQuality" }),
		Workspace = props(workspace, { "Gravity", "FallenPartsDestroyHeight", "StreamingEnabled", "AirDensity", "GlobalWind" }),
		Players = props(game:GetService("Players"), { "CharacterAutoLoads", "RespawnTime", "MaxPlayers" }),
		StarterPlayer = props(game:GetService("StarterPlayer"), { "CameraMode", "EnableMouseLockOption", "CharacterUseJumpPower", "CharacterJumpPower", "CharacterWalkSpeed", "AutoJumpEnabled", "CameraMaxZoomDistance", "CameraMinZoomDistance", "DevComputerMovementMode", "DevTouchMovementMode" }),
		place = { placeId = game.PlaceId, name = game.Name },
		scriptFlags = {},
	}
	for _, root in { RS, SSS, SPS } do
		for _, d in root:GetDescendants() do
			if d:IsA("BaseScript") and (not d.Enabled or (d:IsA("Script") and not d:IsA("LocalScript") and d.RunContext ~= Enum.RunContext.Legacy)) then
				s.scriptFlags[d:GetFullName()] = { Enabled = d.Enabled, RunContext = d:IsA("Script") and d.RunContext.Name or nil }
			end
		end
	end
	return Http:JSONEncode(s)
end

local function roots(): { { path: string, list: { Instance } } }
	local r = {
		{ path = "place/Workspace/Map.Hub.rbxm", list = { workspace.Map.Hub } },
		{ path = "place/Workspace/Map.Rooftop.rbxm", list = { workspace.Map.Rooftop } },
		{ path = "place/Workspace/Map.RooftopV2.rbxm", list = { workspace.Map:FindFirstChild("RooftopV2") } },
		{ path = "place/ServerStorage/JankfireMeshes.rbxm", list = { ST.JankfireMeshes } },
	}
	-- the show hubs built by HubLab (gone once the owner has picked one and the rest are archived)
	local lab = workspace.Map:FindFirstChild("HubLab")
	if lab then table.insert(r, { path = "place/Workspace/Map.HubLab.rbxm", list = { lab } }) end
	-- material variants (JankGrid, the playground tile) and the sky's clouds
	for _, c in game:GetService("MaterialService"):GetChildren() do
		table.insert(r, { path = "place/MaterialService/" .. c.Name .. ".rbxm", list = { c } })
	end
	local clouds = workspace.Terrain:FindFirstChildOfClass("Clouds")
	if clouds then table.insert(r, { path = "place/Workspace/Terrain.Clouds.rbxm", list = { clouds } }) end
	for _, c in RS:GetChildren() do
		if c.Name ~= "Jankfire" then table.insert(r, { path = "place/ReplicatedStorage/" .. c.Name .. ".rbxm", list = { c } }) end
	end
	-- one file per effect / sky, so Rojo can put each back (an .rbxm with several roots can't be a project node)
	for _, c in game:GetService("Lighting"):GetChildren() do table.insert(r, { path = "place/Lighting/" .. c.Name .. ".rbxm", list = { c } }) end
	return r
end

local function b64of(list: { Instance }): string
	return buffer.tostring(Enc:Base64Encode(Ser:SerializeInstancesAsync(list)))
end
local function wrap(items: any): string
	return "JFEXPORT2" .. Http:JSONEncode(items) .. "JFEXPORT_END"
end

local function b64text(s: string): string
	return buffer.tostring(Enc:Base64Encode(buffer.fromstring(s)))
end
-- filler after the end marker: the MCP only saves a result to a file when it is big, and the last slice is short
local function filler(n: number): string
	local t = table.create(n)
	local rng = Random.new(7)
	for i = 1, n do t[i] = string.char(rng:NextInteger(97, 122)) end
	return table.concat(t)
end

function E.run(what: string, arg: any?): string
	local G = _G :: any
	if what == "bundle" then
		-- arg = an optional path prefix, or a list of them: "src/" bundles only the code (a handful of slices),
		-- nil bundles everything
		local prefixes: { string }? = if type(arg) == "string" then { arg } elseif type(arg) == "table" then arg else nil
		local function want(p: string): boolean
			if not prefixes then return true end
			for _, pre in prefixes do if p:sub(1, #pre) == pre then return true end end
			return false
		end
		local items = {}
		for _, it in scripts() do
			if want(it.path) then table.insert(items, { path = it.path, text64 = b64text(it.source) }) end -- base64 keeps it ASCII
		end
		if want("place/settings.json") then table.insert(items, { path = "place/settings.json", text64 = b64text(settings()) }) end
		local sizes = {}
		for _, r in roots() do
			if not want(r.path) then continue end
			local buf = Ser:SerializeInstancesAsync(r.list)
			table.insert(items, { path = r.path, bin64 = buffer.tostring(Enc:Base64Encode(buf)) })
			table.insert(sizes, r.path .. " " .. buffer.len(buf))
			task.wait()
		end
		local s = Http:JSONEncode(items) .. "JFEND"
		G.JFBUNDLE = s
		return ("%d items, %d characters, %d slices\n%s"):format(#items, #s, math.ceil(#s / CHUNK), table.concat(sizes, "\n"))
	elseif what == "slice" then
		local s = G.JFBUNDLE
		if not s then return "NOT BUNDLED: run E.run(\"bundle\") first" end
		local total = math.ceil(#s / CHUNK)
		local i = if type(arg) == "number" then arg else 1
		local piece = s:sub((i - 1) * CHUNK + 1, i * CHUNK)
		local out = ("JFSLICE%04d/%04d:"):format(i, total) .. piece
		if #out < CHUNK then out ..= filler(CHUNK - #out) end
		return out
	elseif what == "done" then
		G.JFBUNDLE = nil; G.JFEXPORT = nil
		return "cleared"
	end
	return "unknown: " .. tostring(what)
end

return E
