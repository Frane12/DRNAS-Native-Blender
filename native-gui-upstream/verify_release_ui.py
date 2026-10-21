#!/usr/bin/env python3
"""Fail CI on untranslated DRNAS menu labels or unwanted release diagnostics."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
activity = (root / "build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java").read_text()
splash = (root / "build_files/android/apk/app/src/main/java/org/blender/blender/DrnasSplashActivity.java").read_text()
gpu = (root / "build_files/android/apk/app/src/main/java/org/blender/blender/DrnasGpuProfile.java").read_text()
native = (root / "intern/ghost/intern/GHOST_WindowAndroid.cc").read_text()

expected_labels = (
    "DRNAS CONTROLS",
    "BUTTON SIZE",
    "BLENDER UI SCALE",
    "Two-finger speed:",
    "UI scale saved. Restart Blender to apply.",
    "Close controls settings",
    "Exit Native Blender?",
    "Setting up Blender for the first time...",
)
visible = activity + splash
for label in expected_labels:
    if label not in visible:
        raise SystemExit(f"Missing release UI label: {label}")

untranslated = (
    "VELIČINA", "kotačić", "tipke", "2 prsta", "brzine",
    "primjena nakon", "ponovnog pokretanja", "spremi položaj",
    "pomakni panel", "iduće pokretanje",
)
for text in untranslated:
    if text in visible:
        raise SystemExit(f"Untranslated menu text in release build: {text}")
if "blender-startup.log" in activity or "announceLogPath" in activity:
    raise SystemExit("Release must not show or create automatic startup logs")
if "Log.i(TAG" in gpu:
    raise SystemExit("Remove routine GPU information logs in release build")
if '__android_log_print(ANDROID_LOG_INFO, "DRNAS-A810"' in native:
    raise SystemExit("Remove routine A810 geometry information logs in release build")
if "Log.w(TAG" not in gpu or 'ANDROID_LOG_WARN, "DRNAS-A810"' not in native:
    raise SystemExit("Do not remove actionable warning logs")
print("PASS: English DRNAS menus, close button and quiet release diagnostics")
