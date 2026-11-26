#!/usr/bin/env python3
"""Pack the working copy's changes to roblox/src scripts as ONE guarded patch module for Studio.

Each changed file becomes (old, new) text pairs: the diff from git <ref> (HEAD by default) to the working file, each old
text widened with context until it is unique in the base and never empty. In Studio the module applies them all or
nothing: every old text must be found exactly once in that script's current Source (so newer work by someone else
makes it refuse, never overwrite). New files (--new) are created, or replaced whole, under their folder.

  py tools/roblox/hunkpatch.py --name WBPatchX --out <dir>/x.rbxm roblox/src/shared/Weapons.luau ... \
     --new roblox/src/client/RopeCut.client.luau

Upload the .rbxm as a Model (Open Cloud), then in Studio (Edit):
  local m = game:GetService("InsertService"):LoadAsset(<id>)
  local mod = m:FindFirstChild("<name>", true); print(require(mod)()); m:Destroy()
(weapons-port, 26 Nov 2026; the earlier copies lived in a scratchpad and were lost)
"""
import argparse, difflib, json, os, re, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ROJO = os.environ.get('ROJO') or os.path.join(os.path.expanduser('~'), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe')
DEST = {'shared': 'ReplicatedStorage.Jankfire', 'client': 'StarterPlayer.StarterPlayerScripts.Jankfire', 'server': 'ServerScriptService.Jankfire'}
L = '======'


def studio_path(rel):
    m = re.match(r'roblox/src/(shared|client|server)/(.+?)(\.client|\.server)?\.luau$', rel.replace('\\', '/'))
    if not m:
        raise SystemExit('not a roblox/src script: ' + rel)
    cls = {'.client': 'LocalScript', '.server': 'Script', None: 'ModuleScript'}[m.group(3)]
    return DEST[m.group(1)], m.group(2), cls


def norm(s):
    return s.replace('\r\n', '\n')


def hunks(base, cur):
    a, b = base.splitlines(keepends=True), cur.splitlines(keepends=True)
    out = []
    for group in difflib.SequenceMatcher(None, a, b, autojunk=False).get_grouped_opcodes(3):
        i1, i2, j1, j2 = group[0][1], group[-1][2], group[0][3], group[-1][4]
        ctx = 0
        while True:
            lo, hi = max(0, i1 - ctx), min(len(a), i2 + ctx)
            old = ''.join(a[lo:hi])
            new = ''.join(a[lo:i1]) + ''.join(b[j1:j2]) + ''.join(a[i2:hi])
            if old and base.count(old) == 1:
                out.append((old, new))
                break
            if lo == 0 and hi == len(a):
                raise SystemExit('could not make a unique hunk')
            ctx += 1
    # overlapping widened hunks would fight: merge any whose old texts overlap in the base
    spans = sorted(((base.index(o), base.index(o) + len(o), o, n) for o, n in out))
    merged = []
    for s, e, o, n in spans:
        if merged and s < merged[-1][1]:
            raise SystemExit('overlapping hunks: lower the context or split the edit')
        merged.append((s, e, o, n))
    return [(o, n) for _, _, o, n in merged]


def lit(s):
    assert (']' + L + ']') not in s
    return '[' + L + '[' + ('\n' if s.startswith('\n') else '') + s + ']' + L + ']'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--new', action='append', default=[])
    # rel=path: take this file's new text from path instead of the working copy (when someone else's uncommitted edits
    # share the file: build HEAD + only your own edits there, and patch from that)
    ap.add_argument('--cur', action='append', default=[])
    ap.add_argument('files', nargs='*')
    o = ap.parse_args()
    lines = ['return function()', "local SES = game:GetService('ScriptEditorService')",
             "local function at(path) local x = game; for seg in string.gmatch(path, '[^%.]+') do x = x and x:FindFirstChild(seg) end; return x end",
             "local function count(s, sub) if sub == '' then return 0 end local n, i = 0, 1; while true do local a, b = string.find(s, sub, i, true); if not a then return n end; n += 1; i = b + 1 end end",
             'local JOBS = {']
    total = 0
    for rel in o.files:
        rel = rel.replace('\\', '/')
        folder, name, _ = studio_path(rel)
        base = norm(subprocess.run(['git', '-C', ROOT, 'show', o.ref + ':' + rel], capture_output=True, text=True, encoding='utf-8', check=True).stdout)
        over = dict(c.split('=', 1) for c in o.cur)
        cur = norm(open(over.get(rel) or os.path.join(ROOT, rel), encoding='utf-8').read())
        hs = hunks(base, cur)
        total += len(hs)
        print(f'{rel}: {len(hs)} hunks')
        lines.append("{ path = '%s.%s', edits = {" % (folder, name))
        for old, new in hs:
            lines.append('{ %s, %s },' % (lit(old), lit(new)))
        lines.append('} },')
    lines.append('}')
    lines.append(r"""local report, plan = {}, {}
for _, j in JOBS do
	local s = at(j.path)
	if not s then table.insert(report, j.path .. ': MISSING'); continue end
	local src = ((s :: any).Source:gsub('\r\n', '\n'))
	local bad = nil
	for i, e in j.edits do
		local n = count(src, e[1])
		if n ~= 1 then bad = ('edit %d matches %d times: %s'):format(i, n, string.sub(e[1], 1, 120)); break end
		local a, b = string.find(src, e[1], 1, true)
		src = string.sub(src, 1, a - 1) .. e[2] .. string.sub(src, b + 1)
	end
	if bad then table.insert(report, j.path .. ': NOT PUSHED, ' .. bad) else table.insert(plan, { s = s, src = src, n = #j.edits, path = j.path }) end
end
if #plan ~= #JOBS then return table.concat(report, string.char(10)) .. string.char(10) .. '(nothing pushed)' end
for _, p in plan do
	SES:UpdateSourceAsync(p.s, function() return p.src end)
	table.insert(report, p.path .. ': ' .. p.n .. ' hunks')
end""")
    for rel in o.new:
        rel = rel.replace('\\', '/')
        folder, name, cls = studio_path(rel)
        src = norm(open(os.path.join(ROOT, rel), encoding='utf-8').read())
        lines.append("do local P = at('%s'); local x = P:FindFirstChild('%s'); if not x then x = Instance.new('%s'); x.Name = '%s'; x.Parent = P end; SES:UpdateSourceAsync(x, function() return %s end); table.insert(report, '%s (%s): ' .. #x.Source .. ' bytes') end"
                     % (folder, name, cls, name, lit(src), name, cls))
    lines.append('return table.concat(report, string.char(10))')
    lines.append('end')
    with tempfile.TemporaryDirectory() as d:
        mod = os.path.join(d, o.name + '.luau')
        open(mod, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        proj = os.path.join(d, 'default.project.json')
        json.dump({'name': o.name + 'Root', 'tree': {'$className': 'Folder', o.name: {'$path': mod.replace('\\', '/')}}}, open(proj, 'w'))
        subprocess.run([ROJO, 'build', proj, '-o', o.out], check=True)
    print('total', total, 'hunks;', len(o.new), 'new files ->', o.out, os.path.getsize(o.out), 'bytes')


if __name__ == '__main__':
    main()
