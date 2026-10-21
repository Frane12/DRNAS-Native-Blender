#!/usr/bin/env python3
import io,json,sys,zipfile
from pathlib import Path
expected=json.loads(Path(__file__).with_name('gpu_drivers.json').read_text())
with zipfile.ZipFile(sys.argv[1]) as z:
    manifest=json.loads(z.read('assets/drnas_gpu_drivers.json'))
    assert len(manifest['drivers'])==10
    assert [e['id'] for e in manifest['drivers']]==[e['id'] for e in expected['drivers']]
    for e in manifest['drivers']:
        lib=z.read('lib/arm64-v8a/'+e['library'])
        assert lib[:5]==b'\x7fELF\x02' and int.from_bytes(lib[18:20],'little')==183
        assert any(n.startswith('assets/gpu-licenses/'+e['id']+'-') for n in z.namelist()),e['id']+' notice missing'
    for name in ('libhook_impl.so','libmain_hook.so','libhardware.so','libcutils.so'):
        assert 'lib/arm64-v8a/'+name in z.namelist(),name
    dex=z.read('classes.dex')
    for token in (b'DrnasGpuOptions',b'DrnasGpuPolicy',b'DrnasInputHold',b'DrnasZoomSpring',b'boot_pending',b'resolution'):
        assert token in dex,token
    lib=z.read('lib/arm64-v8a/libblender.so')
    for token in (b'DRNAS_GPU_DRIVER',b'DRNAS_RENDER_WIDTH',b'DRNAS_GPU_READY_FILE',b'nativeOnDrnasInput'):
        assert token in lib,token
    with zipfile.ZipFile(io.BytesIO(z.read('assets/blender_runtime.zip'))) as runtime:
        for file in ('drnas_native_smooth_zoom.py','drnas_native_save_exit.py'):
            assert any(n.endswith('/'+file) for n in runtime.namelist()),file
print('PASS: ten native drivers, notices, hooks, native integration and every v6 GUI/runtime helper')
