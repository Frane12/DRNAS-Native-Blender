#!/usr/bin/env python3
"""Label and identify a separate DRNAS Android Blender PRE-ALPHA test APK.

Keep org.blender.blender.Java class paths intact (JNI uses this name), and
give this experimental APK its own package so working installations survive.
Not a public release; Blender/upstream attribution remains required.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
base=root/"build_files/android/apk"
manifest=base/"app/src/main/AndroidManifest.xml"
gradle=base/"app/build.gradle"

s=manifest.read_text()
old='android:label="DRNAS Native GUI (Upstream LAB)"'
assert s.count(old)==2,(s.count(old), "Expected application+NativeActivity labels")
s=s.replace(old,'android:label="Blender Native Android Pre-Alpha 2026"')
manifest.write_text(s)
s=gradle.read_text()
oldid="applicationId 'hr.drnas.nativeblendercontrols'"
assert s.count(oldid)==1
s=s.replace(oldid,"applicationId 'hr.drnas.blendernativeprealpha2026'")
oldname="versionName '0.2-native-drnas-touch'"
assert s.count(oldname)==1
s=s.replace(oldname,"versionName '0.3-pre-alpha-2026'")
gradle.write_text(s)
print("PASS: Blender Native Android Pre-Alpha 2026, isolated package")
