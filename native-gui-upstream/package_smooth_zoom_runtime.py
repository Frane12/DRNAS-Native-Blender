#!/usr/bin/env python3
"""Add one startup script; preserve every existing runtime member byte-for-byte."""
from pathlib import Path
import sys
import zipfile

p = Path(sys.argv[1])
script = Path(__file__).with_name('drnas_native_smooth_zoom.py').read_bytes()
compile(script, 'drnas_native_smooth_zoom.py', 'exec')
tmp = p.with_suffix('.new.zip')
name = 'scripts/startup/drnas_native_smooth_zoom.py'
with zipfile.ZipFile(p) as source, zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    assert name not in source.namelist(), 'Unexpected existing startup script'
    for info in source.infolist():
        output.writestr(info, source.read(info.filename))
    output.writestr(name, script)
tmp.replace(p)
print('PASS: runtime gains exactly one Python startup script; all original contents retained')
