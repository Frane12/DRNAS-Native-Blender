#!/usr/bin/env python3
"""Add zoom and safe-exit startup scripts; preserve all original runtime members."""
from pathlib import Path
import sys
import zipfile

p = Path(sys.argv[1])
scripts = {n: Path(__file__).with_name(n).read_bytes() for n in
           ('drnas_native_smooth_zoom.py', 'drnas_native_save_exit.py')}
for name, script in scripts.items():
    compile(script, name, 'exec')
tmp = p.with_suffix('.new.zip')
with zipfile.ZipFile(p) as source, zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    assert not any('scripts/startup/' + n in source.namelist() for n in scripts)
    for info in source.infolist():
        output.writestr(info, source.read(info.filename))
    for name, script in scripts.items():
        output.writestr('scripts/startup/' + name, script)
tmp.replace(p)
print('PASS: two Python startup scripts added; all original runtime contents retained')
