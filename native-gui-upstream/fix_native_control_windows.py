#!/usr/bin/env python3
"""Render DRNAS widgets in app-owned subwindows, never NativeActivity's surface.

Apply last, after the release Java patches. Java-only: existing GHOST JNI is reused.
"""
from pathlib import Path
import re
import sys

activity = Path(sys.argv[1]) / "build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java"
s = activity.read_text()
assert "installDrnasAndroidBack();" in s
assert "drnasAddPanel" not in s, "Window patch already applied"

for name, params in (("bar", "params"), ("view", "lp"), ("speed", "speedPosition"),
                     ("line", "location"), ("options", "settingPosition")):
    old = f"addContentView({name}, {params});"
    assert s.count(old) == 1, old
    s = s.replace(old, f"drnasAddPanel({name}, {params});")

# Translate the WINDOW, not its child: translating a child clips it to the old
# popup rectangle and leaves input at the old position.
s = re.sub(r"\b(view|target|v|line)\.getTranslation([XY])\(\)",
           lambda m: f"drnasOffset{m[2]}({m[1]})", s)
s = re.sub(r"\b(view|target|v|line)\.setTranslation([XY])\(([^;]+)\);",
           lambda m: f"drnasSetOffset{m[2]}({m[1]}, {m[3]});", s)

for name in ("drnasSensitivity", "speed", "options"):
    s = s.replace(f"{name}.setVisibility(", f"drnasPanelVisibility({name}, ")

assert s.count("    super.onPause();") == 1
s = s.replace("    super.onPause();", "    drnasWindowsActive = false;\n    drnasHidePanels();\n    super.onPause();")
assert s.count("    super.onDestroy();") == 1
s = s.replace("    super.onDestroy();", "    drnasWindowsActive = false;\n    drnasHidePanels();\n    drnasPanels.clear();\n    super.onDestroy();")
assert s.count("      enterImmersive();") == 1
s = s.replace("      enterImmersive();", "      enterImmersive();\n      drnasRefreshPanels();")

methods = Path(__file__).with_name("drnas_control_windows.java.inc").read_text()
anchor = "  private void requestAllFilesAccess() {"
assert s.count(anchor) == 1
s = s.replace(anchor, methods + "\n" + anchor)
assert "addContentView(inputView," in s  # keep upstream IME bridge untouched
assert s.count("addContentView(") == 1  # no invisible controls on taken surface
activity.write_text(s)
print("PASS: DRNAS controls use bounded, nonmodal split-touch windows; native binary untouched")
