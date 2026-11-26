# One KeyframeSequence out of a .rbxm, written alone as an .rbxmx (Keyframes, Poses: CFrame, Weight, easing) - ready to
# upload as an Animation asset (open_cloud_invoke assetType "Animation"). Nothing else of the file comes along: no
# scripts, no modules. 26 Nov 2026 (the pro animator's Tidecrest cutscene, kept in the vault, never in git).
#   py -I kfs_to_rbxmx.py <file.rbxm> <sequence name> <out.rbxmx> [--priority N]
import sys, os
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxm_read as R

def f(v): return ('%.6f' % v).rstrip('0').rstrip('.') if v != int(v) else str(int(v))

def write(src, seq_name, out, priority=None):
    ins = R.load(src)
    kfs = next(i for i in ins if i.cls == 'KeyframeSequence' and i.name == seq_name)
    ref = [0]
    def nref():
        ref[0] += 1
        return 'RBX%d' % ref[0]
    L = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
         'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">']
    pri = priority if priority is not None else kfs.props.get('Priority', 5)
    L.append('<Item class="KeyframeSequence" referent="%s"><Properties><bool name="Loop">false</bool><string name="Name">%s</string>'
             '<token name="Priority">%d</token></Properties>' % (nref(), escape(kfs.name), pri))
    def pose(p):
        (x, y, z), r = p.props.get('CFrame', ((0, 0, 0), [1, 0, 0, 0, 1, 0, 0, 0, 1]))
        cf = ''.join('<%s>%s</%s>' % (k, f(v), k) for k, v in zip(('X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22'), (x, y, z, *r)))
        L.append('<Item class="Pose" referent="%s"><Properties><CoordinateFrame name="CFrame">%s</CoordinateFrame>'
                 '<token name="EasingDirection">%d</token><token name="EasingStyle">%d</token><string name="Name">%s</string>'
                 '<float name="Weight">%s</float></Properties>' % (nref(), cf, p.props.get('EasingDirection', 0), p.props.get('EasingStyle', 0),
                                                                  escape(p.name), f(p.props.get('Weight', 1.0))))
        for c in p.children:
            if c.cls == 'Pose': pose(c)
        L.append('</Item>')
    kfs_list = sorted((c for c in kfs.children if c.cls == 'Keyframe'), key=lambda k: k.props.get('Time', 0))
    for k in kfs_list:
        L.append('<Item class="Keyframe" referent="%s"><Properties><string name="Name">%s</string><float name="Time">%s</float></Properties>'
                 % (nref(), escape(k.name or 'Keyframe'), f(k.props.get('Time', 0))))
        for p in k.children:
            if p.cls == 'Pose': pose(p)
        L.append('</Item>')
    L.append('</Item></roblox>')
    open(out, 'w', encoding='utf-8').write(''.join(L))
    return len(kfs_list), ref[0]

if __name__ == '__main__':
    pri = None
    if '--priority' in sys.argv: pri = int(sys.argv[sys.argv.index('--priority') + 1])
    n, refs = write(sys.argv[1], sys.argv[2], sys.argv[3], pri)
    print('wrote', sys.argv[3], n, 'keyframes', refs, 'items', os.path.getsize(sys.argv[3]), 'bytes')
