#!/usr/bin/env python3
"""Wire animated, thread-safe first-setup splash into pinned Blender Java APK."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
java_dir = root / "build_files/android/apk/app/src/main/java/org/blender/blender"
manifest = root / "build_files/android/apk/app/src/main/AndroidManifest.xml"
packager = root / "build_files/android/apk/package.sh"
source = Path(__file__).with_name("DrnasSplashActivity.java")
assert source.is_file()
(java_dir / "DrnasSplashActivity.java").write_text(source.read_text())

m = manifest.read_text()
old_launcher = """            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>"""
assert m.count(old_launcher) == 1, "Launcher declaration changed upstream"
m = m.replace(old_launcher, "", 1)
new_activity = """        <!-- Async runtime extraction + Windows-inspired accelerating horizontal dots.
             NativeActivity is created only AFTER the runtime marker is committed. -->
        <activity
            android:name="org.blender.blender.DrnasSplashActivity"
            android:exported="true"
            android:screenOrientation="sensorLandscape"
            android:theme="@style/Theme.Blender">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
"""
assert m.count("    </application>") == 1
m = m.replace("    </application>", new_activity + "    </application>", 1)
manifest.write_text(m)

s = packager.read_text()
old_java = '"$SCRIPT_DIR/app/src/main/java/org/blender/blender/BlenderActivity.java"'
assert s.count(old_java) == 1, "Upstream javac source list changed"
s = s.replace(old_java, old_java + " \\\n  " +
              '"$SCRIPT_DIR/app/src/main/java/org/blender/blender/DrnasSplashActivity.java"', 1)
packager.write_text(s)

print("PASS: launcher routed to animated splash; both Activity classes compiled into dex")
