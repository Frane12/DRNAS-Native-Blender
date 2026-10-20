#!/usr/bin/env python3
"""Source-level native GHOST support for compact DRNAS keyboard and GUI DPI.

Pin to simfeo/blender commit d93bd33cba768e19ee4387a31c0ea137ee2f0047.
Only the keyboard map and DPI override change, not Vulkan or touch behavior.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
ghost = root / "intern/ghost/intern/GHOST_SystemAndroid.cc"
dpi = root / "intern/ghost/intern/GHOST_AndroidMemoryTier.hh"

def replace_once(s, old, new):
    assert s.count(old) == 1, f"Expected exactly one pinned occurrence: {old[:100]!r}"
    return s.replace(old, new, 1)

s = ghost.read_text()
s = replace_once(s, """    case AKEYCODE_TAB:
      return GHOST_kKeyTab;
    case AKEYCODE_ESCAPE:""", """    case AKEYCODE_TAB:
      return GHOST_kKeyTab;
    /* Compact DRNAS toolbar: keys must be real native GHOST events, not merely
     * visual Android buttons. Handle physical keyboards identically. */
    case AKEYCODE_SHIFT_LEFT:
      return GHOST_kKeyLeftShift;
    case AKEYCODE_SHIFT_RIGHT:
      return GHOST_kKeyRightShift;
    case AKEYCODE_CTRL_LEFT:
      return GHOST_kKeyLeftControl;
    case AKEYCODE_CTRL_RIGHT:
      return GHOST_kKeyRightControl;
    case AKEYCODE_ALT_LEFT:
      return GHOST_kKeyLeftAlt;
    case AKEYCODE_ALT_RIGHT:
      return GHOST_kKeyRightAlt;
    case AKEYCODE_F3:
      return GHOST_kKeyF3;
    case AKEYCODE_F12:
      return GHOST_kKeyF12;
    case AKEYCODE_NUMPAD_1:
      return GHOST_kKeyNumpad1;
    case AKEYCODE_NUMPAD_3:
      return GHOST_kKeyNumpad3;
    case AKEYCODE_NUMPAD_7:
      return GHOST_kKeyNumpad7;
    case AKEYCODE_MOVE_HOME:
      return GHOST_kKeyHome;
    case AKEYCODE_ESCAPE:""")
ghost.write_text(s)

s = dpi.read_text()
s = replace_once(s, """inline uint32_t GHOST_android_ui_dpi()
{
  static const uint32_t dpi = []() -> uint32_t {
    char value[PROP_VALUE_MAX] = {};""", """inline uint32_t GHOST_android_ui_dpi()
{
  static const uint32_t dpi = []() -> uint32_t {
    /* Android Java sets this before NativeActivity startup. Unlike setprop,
     * this works without adb and preserves the chosen UI size across launches. */
    const char *drnas = getenv("DRNAS_ANDROID_UI_DPI");
    if (drnas != nullptr) {
      const int value = atoi(drnas);
      if (value >= 120 && value <= 320) {
        return uint32_t(value);
      }
    }
    char value[PROP_VALUE_MAX] = {};""")
dpi.write_text(s)
print("PASS: native Blender key mappings and persisted JNI-before-GHOST UI DPI")
