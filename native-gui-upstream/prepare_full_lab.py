#!/usr/bin/env python3
"""Apply isolated LAB identity after all accepted Alpha 1.0 patches."""
from pathlib import Path
import shutil
import sys
root = Path(sys.argv[1])
patches = Path(__file__).resolve().parent
app = root / 'build_files/android/apk/app/src/main'
p = app / 'AndroidManifest.xml'
s = p.read_text()
for old, new in (
    ('hr.drnas.blendernativealpha10', 'hr.drnas.blendernativefulllab'),
    ('DRNAS Native Blender Alpha 1.0', 'DRNAS Blender Full LAB'),
    ('1.0-alpha', '1.1-full-lab.1'),
    ('android:versionCode="100"', 'android:versionCode="101"'),
):
    assert old in s, old
    s = s.replace(old, new)
import re
s, count = re.subn(r'android:icon="[^"]+"', 'android:icon="@drawable/drnas_lab_icon"', s)
assert count >= 1
s = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/drnas_lab_icon"', s)
p.write_text(s)
(app / 'res/drawable-nodpi').mkdir(parents=True, exist_ok=True)
shutil.copyfile(patches / 'art/blender-lab.png', app / 'res/drawable-nodpi/drnas_lab_icon.png')
# OIDN requires the separate static Android build; enable in a later LAB revision.
p = root / 'build_files/android/android_features_full.cmake'
s = p.read_text()
assert 'set(WITH_OPENIMAGEDENOISE ON' in s
p.write_text(s.replace('set(WITH_OPENIMAGEDENOISE ON', 'set(WITH_OPENIMAGEDENOISE OFF'))
# Include the Alpha startup helper before signing the newly compiled payload.
p = root / 'build_files/android/apk/package.sh'
s = p.read_text()
anchor = 'echo "[apk] runtime payload:'
assert s.count(anchor) == 1
s = s.replace(anchor, 'python3 "$DRNAS_PATCH_ROOT/package_control_editor_runtime.py" "$ASSETS/blender_runtime.zip"\n' + anchor)
p.write_text(s)
print('PASS: isolated Full LAB identity/icon, Alpha runtime helper, explicit OIDN exclusion')
