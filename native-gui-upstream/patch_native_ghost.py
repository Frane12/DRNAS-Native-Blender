#!/usr/bin/env python3
"""Apply DRNAS native GHOST inputs and touch sensitivity fix to exact upstream tag.

Fail closed on upstream source changes. Under the GPL, the exact upstream
sources and this source-level patch remain freely available to recipients.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
gh = root / "intern/ghost/intern/GHOST_SystemAndroid.hh"
gc = root / "intern/ghost/intern/GHOST_SystemAndroid.cc"
am = root / "intern/ghost/intern/GHOST_AndroidMain.cc"


def once(src: str, old: str, new: str) -> str:
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one occurrence, found {count}: {old[:120]!r}")
    return src.replace(old, new, 1)


h = gh.read_text()
h = once(h, "  void handleJavaKeyEvent(int32_t keycode, int32_t action, int32_t meta_state);",
         """  void handleJavaKeyEvent(int32_t keycode, int32_t action, int32_t meta_state);
  /* UI thread enqueues input; native Blender frame thread emits GHOST events. */
  void handleDrnasInput(int32_t action, float x, float y, float value);""")
h = once(h, "  void drainJavaInput();", """  struct DrnasEvent {
    int32_t action;
    float x, y, value;
  };
  void dispatchDrnasInput(const DrnasEvent &event);
  void drainJavaInput();""")
h = once(h, "  std::vector<JavaKeyEvent> java_keys_;", """  std::vector<JavaKeyEvent> java_keys_;
  std::vector<DrnasEvent> drnas_events_;
  uint32_t drnas_buttons_ = 0;
  float drnas_zoom_remainder_ = 0.0f;
  float drnas_gesture_sensitivity_ = 0.18f;
  float drnas_delta_remainder_x_ = 0.0f;
  float drnas_delta_remainder_y_ = 0.0f;
  float drnas_delta_remainder_zoom_ = 0.0f;""")
gh.write_text(h)

main = am.read_text()
anchor = '/* A .blend tapped in a file manager while Blender runs, from BlenderActivity.onNewIntent'
main = once(main, anchor, """/* JNI is called from Android's UI thread: never push GHOST events here. */
extern "C" JNIEXPORT void JNICALL Java_org_blender_blender_BlenderActivity_nativeOnDrnasInput(
    JNIEnv * /*env*/, jobject /*thiz*/, jint action, jfloat x, jfloat y, jfloat value)
{
  if (GHOST_SystemAndroid *system = android_system_if_ready()) {
    system->handleDrnasInput(action, x, y, value);
  }
}

""" + anchor)
am.write_text(main)

c = gc.read_text()
c = once(c,
    "  gesture_active_ = false;\n\n  /* On proximity exit",
    """  gesture_active_ = false;

  /* DRNAS virtual LMB/RMB: physical finger only moves the cursor while held.
   * Suppress a second finger-triggered click; the virtual button stays held. */
  if (drnas_buttons_ != 0) {
    const int32_t px = int32_t(ghost_android_scale_input(AMotionEvent_getX(event, 0)));
    const int32_t py = int32_t(ghost_android_scale_input(AMotionEvent_getY(event, 0)));
    cursor_x_ = px;
    cursor_y_ = py;
    pushEvent(std::make_unique<GHOST_EventCursor>(
        getMilliSeconds(), GHOST_kEventCursorMove, window_, px, py, GHOST_TABLET_DATA_NONE));
    return 1;
  }

  /* On proximity exit""")

c = once(c, """      gesture_prev_dist_ = dist;
      return 1;
    }

    if (gesture_kind_ == GestureKind::Undecided)""", """      gesture_prev_dist_ = dist;
      drnas_delta_remainder_x_ = 0.0f;
      drnas_delta_remainder_y_ = 0.0f;
      drnas_delta_remainder_zoom_ = 0.0f;
      return 1;
    }

    if (gesture_kind_ == GestureKind::Undecided)""")
c = once(c, """    if (gesture_kind_ == GestureKind::Pan) {
      pushEvent(std::make_unique<GHOST_EventTrackpad>""", """    /* Original upstream passed raw physical deltas from a 2608px+ mobile
     * touchscreen into desktop trackpad navigation. On dense Adreno panels
     * this was far too fast. Scale deltas, preserve subpixel remainders and
     * clamp spikes when touch pointers reorder. Editable via DRNAS SENS. */
    const float speed = drnas_gesture_sensitivity_;
    const auto smooth_delta = [](float delta, float &fraction) -> int32_t {
      fraction += std::max(-12.0f, std::min(12.0f, delta));
      const int32_t step = int32_t(std::trunc(fraction));
      fraction -= float(step);
      return step;
    };
    const int32_t sx = smooth_delta((cx - gesture_prev_x_) * speed,
                                     drnas_delta_remainder_x_);
    const int32_t sy = smooth_delta((cy - gesture_prev_y_) * speed,
                                     drnas_delta_remainder_y_);
    const int32_t sz = smooth_delta((dist - gesture_prev_dist_) * speed,
                                     drnas_delta_remainder_zoom_);
    if (gesture_kind_ == GestureKind::Pan) {
      pushEvent(std::make_unique<GHOST_EventTrackpad>""")
c = once(c, """                                                      int32_t(cx - gesture_prev_x_),
                                                      int32_t(cy - gesture_prev_y_),""",
         """                                                      sx,
                                                      sy,""")
c = once(c, "int32_t(dist - gesture_prev_dist_)", "sz")
c = once(c,
    "void GHOST_SystemAndroid::handleOpenMainFile(const char *path)",
    """void GHOST_SystemAndroid::handleDrnasInput(int32_t action, float x, float y, float value)
{
  if (action < 1 || action > 7) {
    return;
  }
  std::scoped_lock lock(java_input_mutex_);
  /* Bounded queue; never let high-rate UI controls consume unbounded RAM. */
  if (drnas_events_.size() >= 256) {
    drnas_events_.erase(drnas_events_.begin());
  }
  drnas_events_.push_back({action, x, y, value});
}

void GHOST_SystemAndroid::dispatchDrnasInput(const DrnasEvent &event)
{
  if (!window_) {
    return;
  }
  if (event.action == 7) {
    drnas_gesture_sensitivity_ = std::clamp(event.value, 0.08f, 1.0f);
    return;
  }
  if (event.action == 6) {
    drnas_zoom_remainder_ += std::clamp(event.value, -8.0f, 8.0f);
    int count = int(std::trunc(drnas_zoom_remainder_));
    count = std::clamp(count, -5, 5);
    drnas_zoom_remainder_ -= float(count);
    for (int i = 0; i < abs(count); i++) {
      pushEvent(std::make_unique<GHOST_EventWheel>(getMilliSeconds(),
                                                  window_,
                                                  GHOST_kEventWheelAxisVertical,
                                                  count > 0 ? 1 : -1));
    }
    return;
  }
  if (event.action == 1) {
    cursor_x_ = int32_t(ghost_android_scale_input(event.x));
    cursor_y_ = int32_t(ghost_android_scale_input(event.y));
    pushEvent(std::make_unique<GHOST_EventCursor>(getMilliSeconds(),
                                                   GHOST_kEventCursorMove,
                                                   window_, cursor_x_, cursor_y_,
                                                   GHOST_TABLET_DATA_NONE));
    return;
  }
  const bool left = event.action == 2 || event.action == 3;
  const bool down = event.action == 2 || event.action == 4;
  const uint32_t bit = left ? 1u : 2u;
  if (down == ((drnas_buttons_ & bit) != 0)) {
    return;
  }
  touchCancelPending();
  if (down) {
    drnas_buttons_ |= bit;
  }
  else {
    drnas_buttons_ &= ~bit;
  }
  const GHOST_TButton mask = left ? GHOST_kButtonMaskLeft : GHOST_kButtonMaskRight;
  buttons_.set(mask, down);
  pushEvent(std::make_unique<GHOST_EventButton>(
      getMilliSeconds(), down ? GHOST_kEventButtonDown : GHOST_kEventButtonUp,
      window_, mask, GHOST_TABLET_DATA_NONE));
}

void GHOST_SystemAndroid::handleOpenMainFile(const char *path)""")
c = once(c, """  std::vector<JavaKeyEvent> keys;
  std::vector<std::string> open_files;""",
         """  std::vector<JavaKeyEvent> keys;
  std::vector<DrnasEvent> drnas;
  std::vector<std::string> open_files;""")
c = once(c, """    if (java_text_.empty() && java_keys_.empty() && java_open_files_.empty()) {
      return;
    }
    text.swap(java_text_);
    keys.swap(java_keys_);
    open_files.swap(java_open_files_);""",
         """    if (java_text_.empty() && java_keys_.empty() && java_open_files_.empty() &&
        drnas_events_.empty())
    {
      return;
    }
    text.swap(java_text_);
    keys.swap(java_keys_);
    drnas.swap(drnas_events_);
    open_files.swap(java_open_files_);""")
c = once(c, """  for (const JavaKeyEvent &key : keys) {
    dispatchJavaKeyEvent(key.keycode, key.action, key.meta_state);
  }
}""", """  for (const JavaKeyEvent &key : keys) {
    dispatchJavaKeyEvent(key.keycode, key.action, key.meta_state);
  }
  for (const DrnasEvent &event : drnas) {
    dispatchDrnasInput(event);
  }
}""")
c = once(c, "#include <cmath>\n", "#include <cmath>\n#include <algorithm>\n")
gc.write_text(c)
print("PASS: 3 native GHOST sources patched, LMB/RMB/zoom/gesture scaling")
