#!/usr/bin/env python3
import hashlib,io,sys,zipfile
from pathlib import Path
with zipfile.ZipFile(sys.argv[1]) as before,zipfile.ZipFile(sys.argv[2]) as after:
    names={n for n in before.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')}
    assert names=={n for n in after.namelist() if n.startswith(('lib/','assets/')) and not n.endswith('/')}
    for n in names:
        if n=='assets/blender_runtime.zip':
            with zipfile.ZipFile(io.BytesIO(before.read(n))) as a,zipfile.ZipFile(io.BytesIO(after.read(n))) as b:
                extra='scripts/startup/drnas_native_gpu_init.py'
                assert set(b.namelist())==set(a.namelist())|{extra}
                for entry in a.namelist():assert a.read(entry)==b.read(entry),entry
                assert b.read(extra)==Path(__file__).with_name('drnas_native_gpu_init.py').read_bytes()
        else:assert before.read(n)==after.read(n),n
    dex=after.read('classes.dex')
    for token in (b'DrnasInitLog',b'drnasAttachGear',b'drnasOpenGroupEditor',b'keyboard_order',b'keyboard_rows',b'keyboard_width',b'keyboard_height',b'mouse_width',b'mouse_height',b'keyboard_transparency',b'mouse_transparency',b'stretch_screen',b'DrnasInputHold',b'drnasPollSaveExit'):
        assert token in dex,token
    print('Native SHA256:',hashlib.sha256(after.read('lib/arm64-v8a/libblender.so')).hexdigest())
print('PASS: every native binary, GPU driver and original runtime member identical to working v7; UI v8/init report present')
