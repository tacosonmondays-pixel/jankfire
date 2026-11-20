"""Merge an R15 and an R6 KeyframeSequence of the same clip (mixamo_r15.py's .rbxmx, made with and without --r6) into one
animation that plays on both bodies: each keyframe's HumanoidRootPart pose holds the R15 tree (LowerTorso ...) and the
R6 tree (Torso ...) side by side. An Animator only drives the joints its rig has, so an R15 body plays the R15 poses and
an R6 body the R6 ones; one upload serves both (20 Nov 2026, the emotes for R6 bodies).

run:  py -3 tools/blender/merge_r15_r6.py <r15.rbxmx> <r6.rbxmx> <out.rbxm> [--name N]
the .rbxm is built from the merged .rbxmx with Rojo (ROJO, or ~/.aftman/tool-storage/rojo-rbx/rojo/7.7.1/rojo.exe).
"""
import sys, os, json, re, subprocess
import xml.etree.ElementTree as ET

a, b, out = sys.argv[1], sys.argv[2], sys.argv[3]
name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else os.path.basename(out).rsplit('.', 1)[0]
A, B = ET.parse(a), ET.parse(b)

def keyframes(tree):
    seq = tree.getroot().find('Item')
    return seq, [it for it in seq.findall('Item') if it.get('class') == 'Keyframe']

def time_of(kf):
    return float(kf.find('Properties/float[@name="Time"]').text)

def root_pose(kf):
    return next(it for it in kf.findall('Item') if it.get('class') == 'Pose')

seqA, kfA = keyframes(A)
_, kfB = keyframes(B)
ref = [0]
def renum(el):
    for it in el.iter('Item'):
        ref[0] += 1
        it.set('referent', 'RBXM%08X' % ref[0])
# (keyframes paired by time: the two runs can disagree by one frame on whether a clip already loops, 66_salsa_male_8;
# an R15 keyframe with no R6 twin takes the nearest R6 one)
byTime = sorted(((time_of(y), y) for y in kfB), key=lambda p: p[0])
def nearest(t):
    lo, hi = 0, len(byTime) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if byTime[mid][0] < t: lo = mid + 1
        else: hi = mid
    best = min((i for i in (lo - 1, lo) if 0 <= i < len(byTime)), key=lambda i: abs(byTime[i][0] - t))
    return byTime[best][1]
import copy
for x in kfA:
    y = nearest(time_of(x))
    ra, rb = root_pose(x), copy.deepcopy(root_pose(y))
    for child in [c for c in rb.findall('Item') if c.get('class') == 'Pose']:
        renum(child)
        ra.append(child)
seqA.find('Properties/string[@name="Name"]').text = name
xml_path = out + 'x' if out.lower().endswith('.rbxm') else out
A.write(xml_path, encoding='utf-8', xml_declaration=False)
if out.lower().endswith('.rbxm'):
    rojo = os.environ.get('ROJO') or os.path.join(os.path.expanduser('~'), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe')
    proj = out + '.project.json'
    open(proj, 'w', encoding='utf-8').write(json.dumps({ 'name': name, 'tree': { '$path': os.path.basename(xml_path) } }))
    subprocess.run([rojo, 'build', proj, '-o', out], check=True, cwd=os.path.dirname(os.path.abspath(out)))
    os.remove(proj)
print('MERGED', name, len(kfA), 'keyframes')
