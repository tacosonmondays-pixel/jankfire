--!strict
--!native
-- SHA-256 (FIPS 180-4) in plain Luau, for the lore codes' hashes (LoreCodeBook): Sha256.hex(s) -> 64 hex digits.
-- Matches Python's hashlib.sha256(s.encode()).hexdigest() (the round constants below were worked out from the primes
-- by the tool that wrote this file, scratchpad make_codes.py). Server only. Sha256.hex("abc") =
-- ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
local K = {
	0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
}
local H0 = {
	0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
}
local M = 0x100000000

local Sha256 = {}

function Sha256.hex(msg: string): string
	local len = #msg
	local padLen = ((len + 9 + 63) // 64) * 64
	local b = buffer.create(padLen)
	buffer.writestring(b, 0, msg)
	buffer.writeu8(b, len, 0x80)
	local bits = len * 8
	local hi, lo = bits // M, bits % M
	for i = 0, 3 do
		buffer.writeu8(b, padLen - 8 + i, bit32.extract(hi, (3 - i) * 8, 8))
		buffer.writeu8(b, padLen - 4 + i, bit32.extract(lo, (3 - i) * 8, 8))
	end
	local h = table.clone(H0)
	local w = table.create(64, 0)
	for at = 0, padLen - 1, 64 do
		for i = 0, 15 do
			local o = at + i * 4
			w[i + 1] = bit32.bor(bit32.lshift(buffer.readu8(b, o), 24), bit32.lshift(buffer.readu8(b, o + 1), 16),
				bit32.lshift(buffer.readu8(b, o + 2), 8), buffer.readu8(b, o + 3))
		end
		for i = 17, 64 do
			local x, y = w[i - 15], w[i - 2]
			local s0 = bit32.bxor(bit32.rrotate(x, 7), bit32.rrotate(x, 18), bit32.rshift(x, 3))
			local s1 = bit32.bxor(bit32.rrotate(y, 17), bit32.rrotate(y, 19), bit32.rshift(y, 10))
			w[i] = (w[i - 16] + s0 + w[i - 7] + s1) % M
		end
		local a, bb, c, d, e, f, g, hh = h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8]
		for i = 1, 64 do
			local S1 = bit32.bxor(bit32.rrotate(e, 6), bit32.rrotate(e, 11), bit32.rrotate(e, 25))
			local ch = bit32.bxor(bit32.band(e, f), bit32.band(bit32.bnot(e), g))
			local t1 = (hh + S1 + ch + K[i] + w[i]) % M
			local S0 = bit32.bxor(bit32.rrotate(a, 2), bit32.rrotate(a, 13), bit32.rrotate(a, 22))
			local maj = bit32.bxor(bit32.band(a, bb), bit32.band(a, c), bit32.band(bb, c))
			local t2 = (S0 + maj) % M
			hh, g, f, e, d, c, bb, a = g, f, e, (d + t1) % M, c, bb, a, (t1 + t2) % M
		end
		h[1] = (h[1] + a) % M; h[2] = (h[2] + bb) % M; h[3] = (h[3] + c) % M; h[4] = (h[4] + d) % M
		h[5] = (h[5] + e) % M; h[6] = (h[6] + f) % M; h[7] = (h[7] + g) % M; h[8] = (h[8] + hh) % M
	end
	return string.format("%08x%08x%08x%08x%08x%08x%08x%08x", h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8])
end

return Sha256
