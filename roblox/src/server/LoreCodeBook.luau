--!strict
-- THE LORE CODES (18 Nov 2026, the owner: "there should be a control panel somewhere that you type in jank actually
-- make codes and every code spawns in an NPC, ill give the codes weekly by weekly at some point"). One code per hidden
-- NPC and one for the hub egg's mannequin. HASHES ONLY: the plain codes are in the owner's vault (JANKFIRE Vault,
-- Codes.md), never in git or the game. A code is checked by LoreNPCs.server: the typed text made plain (lower case,
-- letters and digits only, so "Jank Cola", "JANKCOLA" and " jank-cola " would be one code), then
--   h = sha256(SALT .. ":" .. plain), then ITER - 1 times h = sha256(h .. SALT)   (Sha256.luau; hex digits)
-- and compared with every row whose `opens` day (UTC, from midnight) has come. Before its day a code is just wrong.
-- TO MOVE A WEEK: change `opens` here (and in the vault list). TO CHANGE A CODE: re-run the scratchpad tool
-- (make_codes.py) or hash it the same way: Python
--   h = sha256((SALT + ":" + plain).encode()).hexdigest(); for _ in range(ITER - 1): h = sha256((h + SALT).encode()).hexdigest()
-- Server only (ServerScriptService): never in ReplicatedStorage.
local B = {}
B.SALT = "0ae3c0de873051b043795ad9ac8392c2"
B.ITER = 100
B.CODES = {
	{ id = "egg", opens = "2026-11-18", hash = "dd38951f7cef0f2803f7cc6aad5591dc8141eb6e1e09f0c7648b4d0df7bbcb81" },
	{ id = "gary", opens = "2026-11-23", hash = "7da1dfa31d8109c7d06a91450df1a906eb255c631a4b108e93ed05e254ec27d2" },
	{ id = "dale", opens = "2026-11-30", hash = "b0b77b9520dbf9e52d2d518ea3d1e4de1ec26bd5763ff44d23d9aa84f58bea02" },
	{ id = "janitor", opens = "2026-12-07", hash = "5ca0f240fce8ecfe5b0635ce0980b5e30efd3dfc44d220c71055ac50dc138e7d" },
	{ id = "smiles", opens = "2026-12-14", hash = "fe086f610fec57fb9eacb6d7d7c808999fcf6bf2d2d88f4283c4e6ad6d7da8db" },
	{ id = "todd", opens = "2026-12-21", hash = "1a3803e3ab43ebff14b0464e4d2a3af63c1224ba752fa6be654fbe6ad93bf3c8" },
	{ id = "auntie", opens = "2026-12-28", hash = "6fd8b11d6e98f3a726a741b028777a699f838f161f75d217328a77b9db08ff0b" },
	{ id = "lumps", opens = "2027-01-04", hash = "5f905b04279d2a1870f421a264da14ef24b100f7779013eee40ecc3c246f4237" },
	{ id = "gordo", opens = "2027-01-11", hash = "6174fb2abbb550ef6ba0b3f3a7309b9e361461e2e762595c0f893b676bf53ce4" },
	{ id = "mina", opens = "2027-01-18", hash = "09ac6bc58ca851d3ad6705864e396ac3e3fcc8ef008259916e779ed81d517fbb" },
	{ id = "sharon", opens = "2027-01-25", hash = "1c036e605b55ce76b445fb309f71b2c11b8ba95962e9085e4f2af582b832fbe0" },
	{ id = "dumpling", opens = "2027-02-01", hash = "1e3bcc73e5da81e084f90d4aeba2f89b7ac5cb53dc375c68fa4c69019d5c83cc" },
	{ id = "pallet_jack", opens = "2027-02-08", hash = "fe051f14e94ddda7462f96031cc070f2f2fb4f5eac6189cd6c3eb9f0f57325ff" },
	{ id = "eotm", opens = "2027-02-15", hash = "6932cf293124aff9d3e53061bf58b3c886325d4af3f3ca249d3b00d644952d55" },
	{ id = "overtime", opens = "2027-02-22", hash = "11077d7956c1a1800f5b2c12865de121058cc203a30153a91d2854f58cc9c255" },
	{ id = "hr", opens = "2027-03-01", hash = "d05bbb767a70f0304849dcb275da32b291dc7ad23d3b955da0854e66118b6054" },
} :: { { id: string, opens: string, hash: string } }
return B
