#!/usr/bin/env python3
"""Reject any Java-only controls APK that changes native or runtime payloads."""
import hashlib
import subprocess
import sys
import tempfile
import zipfile

with zipfile.ZipFile(sys.argv[1]) as original, zipfile.ZipFile(sys.argv[2]) as output:
    payloads = {n for n in original.namelist() if n.startswith(("lib/", "assets/")) and not n.endswith("/")}
    actual = {n for n in output.namelist() if n.startswith(("lib/", "assets/")) and not n.endswith("/")}
    assert payloads == actual, "Native/runtime file list changed"
    for name in sorted(payloads):
        assert hashlib.sha256(original.read(name)).digest() == hashlib.sha256(output.read(name)).digest(), name
    dex = output.read("classes.dex")
    for name in (b"Landroid/widget/PopupWindow;", b"drnasAddPanel", b"setTouchModal",
                 b"setSplitTouchEnabled", b"nativeOnDrnasInput", b"installDrnasControls"):
        assert name in dex, f"Missing packaged controls: {name!r}"
    with tempfile.NamedTemporaryFile(suffix=".so") as lib:
        lib.write(output.read("lib/arm64-v8a/libblender.so"))
        lib.flush()
        symbols = subprocess.check_output(["readelf", "--dyn-syms", "--wide", lib.name], text=True)
        for name in ("nativeOnDrnasInput", "nativeOnKey"):
            assert "Java_org_blender_blender_BlenderActivity_" + name in symbols, name
print(f"PASS: {len(payloads)} unchanged native/runtime files; popup controls in DEX; existing JNI exports verified")
