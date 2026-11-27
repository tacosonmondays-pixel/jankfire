--!strict
-- CullKeep (27 Nov 2026): how a film (or anything else on this client) tells ZoneCull to keep map pieces drawn while
-- it plays. ZoneCull puts every big piece of workspace.Map aside unless your body or camera is near it; a film's lens
-- cuts to places your body isn't, and a piece that comes back on the cut frame pops in while the shot plays (the owner,
-- 27 Nov: "Things pop in because it renders as the clip plays"). An ask names pieces, or points that count as near
-- (exactly like the camera: within ZoneCull's margin of the piece's box), for a while or until it is released.
--   CullKeep.keep(key, { names = { "TrainingGround" }?, points = { Vector3 }?, seconds = n? })   (same key: replaced)
--   CullKeep.release(key)
--   CullKeep.pieces(points?, names?) -> { Instance }   the pieces those points/names keep (shown or still put aside),
--     from ZoneCull's own list (empty if ZoneCull isn't running)
-- CineKit.prewarm does all of this for a film: keep, wait for the pieces to come back, preload what they use.
-- ZoneCull reads the asks every step (roblox/src/client/ZoneCull.client.luau, roblox/docs/PERFORMANCE.md).
local K = {}
export type Ask = { names: { [string]: boolean }, points: { Vector3 }, untilT: number? }
K.asks = {} :: { [string]: Ask }
-- (ZoneCull fills this in: given points and names, its pieces that they keep)
K.lookup = nil :: ((points: { Vector3 }, names: { [string]: boolean }) -> { Instance })?

function K.keep(key: string, spec: { names: { string }?, points: { Vector3 }?, seconds: number? })
	local names = {}
	for _, n in spec.names or {} do names[n] = true end
	K.asks[key] = { names = names, points = table.clone(spec.points or {}), untilT = if spec.seconds then os.clock() + spec.seconds else nil }
end

function K.release(key: string)
	K.asks[key] = nil
end

-- the live asks (expired ones dropped): every name and every point any of them holds
function K.all(): ({ [string]: boolean }, { Vector3 })
	local names, points = {}, {}
	local now = os.clock()
	for key, a in K.asks do
		if a.untilT and now > a.untilT then K.asks[key] = nil; continue end
		for n in a.names do names[n] = true end
		for _, p in a.points do table.insert(points, p) end
	end
	return names, points
end

function K.pieces(points: { Vector3 }?, names: { string }?): { Instance }
	if not K.lookup then return {} end
	local set = {}
	for _, n in names or {} do set[n] = true end
	return K.lookup(points or {}, set)
end

return K
