#!/usr/bin/env python3
"""Label and identify a separate DRNAS Android Blender PRE-ALPHA test APK.

Keep org.blender.blender.Java class paths intact (JNI uses this name), and
give this experimental APK its own package so working installations survive.
Public pre-release builds must include Blender/upstream attribution and license.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
base=root/"build_files/android/apk"
manifest=base/"app/src/main/AndroidManifest.xml"
gradle=base/"app/build.gradle"

s=manifest.read_text()
old='android:label="DRNAS Native GUI (Upstream LAB)"'
assert s.count(old)>=2,(s.count(old), "Expected application+NativeActivity labels")
s=s.replace(old,'android:label="Native Blender PreAlpha 0.1"')
# The pinned Android build uses package.sh + aapt2 directly; Gradle versionName
# is NOT used to package the APK. Put it in the actual Android manifest.
manifest_package = 'package="org.blender.blender"'
assert s.count(manifest_package) == 1, "Pinned manifest package changed"
s=s.replace(manifest_package,
            'package="org.blender.blender" android:versionCode="1" android:versionName="0.1.0"', 1)
assert 'android:versionName="0.1.0"' in s
manifest.write_text(s)
s=gradle.read_text()
oldid="applicationId 'hr.drnas.nativeblendercontrols'"
assert s.count(oldid)==1
s=s.replace(oldid,"applicationId 'hr.drnas.blendernativeprealpha2026'")
oldname="versionName '0.2-native-drnas-touch'"
assert s.count(oldname)==1
s=s.replace(oldname,"versionName '0.1.0'")
gradle.write_text(s)
print("PASS: Native Blender PreAlpha 0.1, isolated package")
