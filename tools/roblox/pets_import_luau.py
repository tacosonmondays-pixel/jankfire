# writes roblox/studio-tools/PetImport.luau's LAYOUT table from pets_models.py's pets_layout.json (the joints and
# where each piece's middle is), between the "-- LAYOUT BEGIN" / "-- LAYOUT END" lines. run after pets_models.py:
#   py -3 tools/roblox/pets_import_luau.py <out_dir>/pets_layout.json
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DST = os.path.join(REPO, 'roblox', 'studio-tools', 'PetImport.luau')
L = json.load(open(sys.argv[1]))

def v3(v): return 'Vector3.new(%s, %s, %s)' % tuple(('%.4f' % x).rstrip('0').rstrip('.') if x else '0' for x in v)

rows = ['I.LAYOUT = {']
for pet in ('mannequin', 'kennel'):  # (the dog and the slug are skinned since take 2: pets_skinned.py, I.SKINNED)
    d = L[pet]
    ex = d['extra']
    extra = ''
    if 'feet' in ex: extra += ', feet = %.4f' % ex['feet']
    if 'door' in ex: extra += ', door = %s' % v3(ex['door'])
    rows.append('\t%s = { size = %s%s, pieces = {' % (pet, v3(d['size']), extra))
    for name, p in d['pieces'].items():
        bits = ['role = "%s"' % p['role'], 'joint = %s' % v3(p['joint']), 'centre = %s' % v3(p['centre'])]
        if 'side' in p: bits.append('side = %d' % p['side'])
        if 'front' in p: bits.append('front = %s' % ('true' if p['front'] else 'false'))
        if 'n' in p: bits.append('n = %d' % p['n'])
        rows.append('\t\t%s = { %s },' % (name, ', '.join(bits)))
    rows.append('\t} },')
rows.append('}')
src = open(DST, encoding='utf-8').read()
new = re.sub(r'-- LAYOUT BEGIN\n.*?-- LAYOUT END', '-- LAYOUT BEGIN\n' + '\n'.join(rows) + '\n-- LAYOUT END', src, flags=re.S)
open(DST, 'w', encoding='utf-8', newline='\n').write(new)
print('PetImport LAYOUT:', len(rows), 'lines')
