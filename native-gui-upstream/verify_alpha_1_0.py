#!/usr/bin/env python3
"""Fail fast if first-run stretch, language menu, identity, or native baseline drift."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
java=root/"build_files/android/apk/app/src/main/java/org/blender/blender"
activity=(java/"BlenderActivity.java").read_text()
gpu=(java/"DrnasGpuOptions.java").read_text()
lang=(java/"DrnasLanguage.java").read_text()
manifest=(root/"build_files/android/apk/app/src/main/AndroidManifest.xml").read_text()

def expect(condition, message):
    if not condition:
        raise SystemExit("Alpha 1.0 release UI validation failed: "+message)

expect('drnasInstallLanguageMenu(optionRows)' in activity,"missing language picker in real settings menu")
expect('putString("drnas_language", selected)' in activity,"language selection not persisted")
expect('"drnas_language", "en"' in lang,"English not the default")
expect('"hr".equals(current(context))' in lang,"Croatian not selectable")
expect('getBoolean("stretch_screen",true)' in gpu,"Stretch is not ON by default")
expect('!stretchPrefs.contains("stretch_screen")' in gpu,"fresh-install preference migration missing")
expect('putBoolean("stretch_screen",true).commit()' in gpu,"Stretch preference must be persisted")
expect('applyStretch(a);' in gpu,"Stretch must be applied at startup")
expect('stretchPrefs.edit().putBoolean("stretch_screen",true)' in gpu,"fresh start preference must be preserved")
expect('hr.drnas.blendernativealpha10' in manifest,"wrong Alpha package name")
expect('1.0-alpha' in manifest,"wrong versionName")
expect('DRNAS Native Blender Alpha 1.0' in manifest,"wrong Alpha label")
expect('nativeOnCommitText' in activity,"IME text bridge lost")
expect('drnasNativePointerX' in activity,"v10 stretch pointer mapping lost")
expect('drnasCompactMouseWindow' in activity,"floating mouse window lost")

# Explicit important English UI surface checks. Other translations are
# selected by DrnasLanguage, not by Android's system locale.
for label in (
    '"English"', '"Hrvatski"', '"Relative mouse / touchpad (off: direct touch)"',
    '"Mouse speed: "', '"Mouse and zoom"', '"Group width"', '"Group height"',
    '"DRNAS LANGUAGE (restart to apply)"', '"Save and Exit"',
    '"RESOLUTION • keep aspect ratio"', '"System Vulkan (default)"',
):
    expect(label in (activity+gpu),f"missing English locale option: {label}")

# Critical Croatian strings must be dynamic alternatives, never sole UI labels.
for phrase in (
    '"Miš / touchpad (isključeno: direktni dodir)"',
    '"Spremi i izađi"',
    '"Širina grupe"',
):
    expect('DrnasLanguage.text(' in activity,"missing locale-aware labels")
    expect(phrase in activity,"missing Croatian alternative "+phrase)

print("PASS: English default, Croatian menu switch, first-launch Stretch ON, Alpha 1.0 identity and v10 controls")
