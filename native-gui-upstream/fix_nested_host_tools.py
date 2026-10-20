#!/usr/bin/env python3
"""Make upstream Blender's nested host code generators truly headless.

The Android CMake configuration forwards all WITH_* variables into host_tools.
It incorrectly forwards desktop X11/SDL and Android GHOST flags to the native
Linux code generators. The outer host tools (which our build_apk.sh already
builds) successfully use WITH_HEADLESS=ON. Apply the same configuration to
the nested host_tools, retaining feature flags relevant to DNA/RNA.
"""
from pathlib import Path
import sys

file = Path(sys.argv[1]) / "build_files/cmake/host_tools.cmake"
src = file.read_text()
needle = "  set(_host_tools_targets\n"
if src.count(needle) != 1:
    raise SystemExit("Unexpected host_tools.cmake, refusing to patch")
patch = """  # DRNAS Android cross-build: this subproject runs on a Linux CI runner.
  # It must not build the Android GHOST or demand X11 development packages.
  # Override the forwarded target flags AFTER they have been appended.
  list(APPEND _host_tools_forwarded_args
    "-DWITH_HEADLESS=ON"
    "-DWITH_GHOST_ANDROID=OFF"
    "-DWITH_GHOST_X11=OFF"
    "-DWITH_X11=OFF"
    "-DWITH_GHOST_WAYLAND=OFF"
    "-DWITH_GHOST_SDL=OFF"
    "-DWITH_X11_XINPUT=OFF"
    "-DWITH_AUDASPACE=OFF"
  )

"""
file.write_text(src.replace(needle,patch+needle,1))
print("PASS: nested Blender host code generators configured headless (no X11)")
