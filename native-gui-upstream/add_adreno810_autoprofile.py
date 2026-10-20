#!/usr/bin/env python3
"""Copy GPU profile and wire A810 auto-selection before NativeActivity startup."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
app = root / "build_files/android/apk"
activity = app / "app/src/main/java/org/blender/blender/BlenderActivity.java"
gpu_java = app / "app/src/main/java/org/blender/blender/DrnasGpuProfile.java"
package = app / "package.sh"

def once(s, old, new):
    assert s.count(old) == 1, f"Expected pinned source exactly once: {old!r}"
    return s.replace(old, new, 1)

gpu_java.write_text(Path(__file__).with_name("DrnasGpuProfile.java").read_text())

s=activity.read_text()
s=once(s, "    publishLaunchFile(getIntent());\n",
       """    /* Run before super.onCreate: NativeActivity creates the Vulkan window. */
    DrnasGpuProfile.apply(this);
    publishLaunchFile(getIntent());
""")
activity.write_text(s)

s=package.read_text()
old='"$SCRIPT_DIR/app/src/main/java/org/blender/blender/DrnasSplashActivity.java"'
new=old+' \\\n  "$SCRIPT_DIR/app/src/main/java/org/blender/blender/DrnasGpuProfile.java"'
s=once(s,old,new)
package.write_text(s)
print("PASS: runtime EGL renderer detection wired before native Vulkan startup")
