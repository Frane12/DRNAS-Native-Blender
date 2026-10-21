#!/usr/bin/env python3
"""Reject any Java-only controls APK that changes native or runtime payloads."""
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

with zipfile.ZipFile(sys.argv[1]) as original, zipfile.ZipFile(sys.argv[2]) as output:
    payloads = {n for n in original.namelist() if n.startswith(("lib/", "assets/")) and not n.endswith("/")}
    actual = {n for n in output.namelist() if n.startswith(("lib/", "assets/")) and not n.endswith("/")}
    assert payloads == actual, "Native/runtime file list changed"
    for name in sorted(payloads):
        if name == 'assets/blender_runtime.zip' and '--smooth-runtime' in sys.argv:
            with zipfile.ZipFile(io.BytesIO(original.read(name))) as before, zipfile.ZipFile(io.BytesIO(output.read(name))) as after:
                added = {'scripts/startup/drnas_native_smooth_zoom.py'}
                if '--save-exit' in sys.argv:
                    added.add('scripts/startup/drnas_native_save_exit.py')
                assert set(after.namelist()) == set(before.namelist()) | added
                for entry in before.namelist():
                    assert before.read(entry) == after.read(entry), entry
                for name in added:
                    assert after.read(name) == Path(__file__).with_name(Path(name).name).read_bytes()
            continue
        assert hashlib.sha256(original.read(name)).digest() == hashlib.sha256(output.read(name)).digest(), name
    dex = output.read("classes.dex")
    for name in (b"Landroid/widget/PopupWindow;", b"drnasAddPanel", b"setTouchModal",
                 b"setSplitTouchEnabled", b"nativeOnDrnasInput", b"installDrnasControls"):
        assert name in dex, f"Missing packaged controls: {name!r}"
    if "--emu" in sys.argv:
        for name in (b"DrnasTrackpad", b"relative_mouse", b"pointer_effect", b"mouse_speed",
                     b"Box Select", b"Select All", b"Play/Pause", b"Keyboard"):
            assert name in dex, f"Missing EMU control option: {name!r}"
    if '--smooth-runtime' in sys.argv:
        assert b'drnasOfferZoom' in dex and b'shortcut_expanded' in dex
    if '--spring' in sys.argv:
        for name in (b'DrnasZoomSpring', b'drnasMouseRoot', b'drnasStopSpringZoom', b'Zatvori postavke'):
            assert name in dex, f'Missing spring/multitouch/settings feature: {name!r}'
    if '--save-exit' in sys.argv:
        for name in (b'drnasSaveAndExit', b'drnasPollSaveExit', b'cursor_percent', b'zoom_visible', b'drnasStyleKey'):
            assert name in dex, f'Missing polished controls or safe exit: {name!r}'
    if '--latch' in sys.argv:
        for name in (b'DrnasInputHold', b'drnasMouseButtonSizes', b'mouse_button_percent', b'drnasReleaseAllInputs'):
            assert name in dex, f'Missing input latch or separate sizing: {name!r}'
    with tempfile.NamedTemporaryFile(suffix=".so") as lib:
        lib.write(output.read("lib/arm64-v8a/libblender.so"))
        lib.flush()
        symbols = subprocess.check_output(["readelf", "--dyn-syms", "--wide", lib.name], text=True)
        for name in ("nativeOnDrnasInput", "nativeOnKey"):
            assert "Java_org_blender_blender_BlenderActivity_" + name in symbols, name
print('PASS: all native libraries identical; runtime originals unchanged; permitted smooth-zoom startup verified; controls/JNI verified')
