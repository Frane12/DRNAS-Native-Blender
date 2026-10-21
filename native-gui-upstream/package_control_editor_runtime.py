#!/usr/bin/env python3
"""Add exactly one init report script to accepted GPU v7 runtime; retain every member."""
from pathlib import Path
import sys,zipfile
p=Path(sys.argv[1]);tmp=p.with_suffix('.ui8.tmp.zip')
with zipfile.ZipFile(p) as before,zipfile.ZipFile(tmp,'w') as after:
    for entry in before.infolist():after.writestr(entry,before.read(entry.filename))
    name='scripts/startup/drnas_native_gpu_init.py'
    assert name not in before.namelist()
    after.writestr(name,Path(__file__).with_name('drnas_native_gpu_init.py').read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
tmp.replace(p)
print('PASS: preserved complete GPU v7 runtime, added bounded init report only')
