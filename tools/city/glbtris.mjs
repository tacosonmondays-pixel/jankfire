// Triangle count of each story model: node tools/city/glbtris.mjs [dir]
import fs from 'node:fs';
const dir = process.argv[2] || 'public/models/story';
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.glb')).sort()) {
  const b = fs.readFileSync(dir + '/' + f), len = b.readUInt32LE(12), j = JSON.parse(b.slice(20, 20 + len).toString());
  let tris = 0; const mats = new Set();
  for (const m of j.meshes || []) for (const p of m.primitives) { const a = j.accessors[p.indices ?? p.attributes.POSITION]; tris += (p.indices !== undefined ? a.count : a.count) / 3; if (p.material !== undefined) mats.add(j.materials[p.material].name); }
  console.log(f.padEnd(26), String(Math.round(tris)).padStart(6), 'tris', String(Math.round(b.length / 1024)).padStart(5), 'KB', [...mats].join(','));
}
