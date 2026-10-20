#!/usr/bin/env python3
"""Adreno 810-only GPU render budget, preserving A840 and all other GPUs.

The Java launcher detects *GPU renderer*, NOT Snapdragon model number, via
EGL GLES_RENDERER before NativeActivity begins. It sets DRNAS_A810_RENDER_LIMIT=1
only for GPU string 'Adreno (TM) 810' (or equivalent). With that opt-in, native
Blender Vulkan surface buffers fit inside 960x544 without aspect distortion.
Android's full-screen display stays unchanged; touch is mapped into reduced
Vulkan buffer coordinates. Other GPUs retain the upstream path unchanged.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
memory = root / "intern/ghost/intern/GHOST_AndroidMemoryTier.hh"
win = root / "intern/ghost/intern/GHOST_WindowAndroid.cc"
sys_file = root / "intern/ghost/intern/GHOST_SystemAndroid.cc"

def once(s, old, new):
    assert s.count(old) == 1, f"Expected unique pinned match: {old[:96]!r} (found {s.count(old)})"
    return s.replace(old, new, 1)

m = memory.read_text()
m = once(m, "#  include <cstdlib>\n", "#  include <cstdlib>\n#  include <atomic>\n#  include <algorithm>\n#  include <cstdint>\n")
m = once(m, """/** Divisor applied to the native window size. 1 = native, 2 = half resolution. */""",
r"""/* The GPU is classified in Java before the native main starts; the upstream
 * window code is Vulkan-only, so no runtime GL context is retained. */
inline bool GHOST_android_drnas_a810_enabled()
{
  const char *flag = getenv("DRNAS_A810_RENDER_LIMIT");
  return flag && flag[0] == '1' && flag[1] == '\0';
}

/* Desired Vulkan buffer size. Fit, NEVER stretch: 960x544 is an upper bound,
 * not a forced aspect ratio. Height may be lower on 20:9 phone screens. */
inline void GHOST_android_drnas_a810_size(int32_t native_w,
                                          int32_t native_h,
                                          int32_t &out_w,
                                          int32_t &out_h)
{
  out_w = native_w;
  out_h = native_h;
  if (!GHOST_android_drnas_a810_enabled() || native_w <= 0 || native_h <= 0) {
    return;
  }
  const float factor = std::min(1.0f,
                                std::min(960.0f / float(native_w),
                                         544.0f / float(native_h)));
  if (factor >= 1.0f) {
    return;
  }
  out_w = std::max(2, (int32_t(native_w * factor) / 2) * 2);
  out_h = std::max(2, (int32_t(native_h * factor) / 2) * 2);
}

/* GHOST receives physical touch coordinates: convert to smaller Vulkan viewport.
 * Singleton atomic lives across source translation units; updating it when the
 * actual window size changes is lock-free and requires no app restart. */
inline std::atomic<float> &GHOST_android_drnas_touch_ratio()
{
  static std::atomic<float> ratio{1.0f};
  return ratio;
}

/** Divisor applied to the native window size. 1 = native, 2 = half resolution. */""")
m = once(m, """  static const uint32_t divisor = []() -> uint32_t {
    char value[PROP_VALUE_MAX] = {};""",
"""  static const uint32_t divisor = []() -> uint32_t {
    if (GHOST_android_drnas_a810_enabled()) {
      return 1; /* A810 uses exact aspect-correct width/height, not divisor. */
    }
    char value[PROP_VALUE_MAX] = {};""")
m = once(m, """inline float ghost_android_scale_input(float value)
{
  const uint32_t divisor = GHOST_android_render_scale_divisor();""",
"""inline float ghost_android_scale_input(float value)
{
  if (GHOST_android_drnas_a810_enabled()) {
    return value * GHOST_android_drnas_touch_ratio().load(std::memory_order_relaxed);
  }
  const uint32_t divisor = GHOST_android_render_scale_divisor();""")
memory.write_text(m)

w = win.read_text()
w = once(w, """static void ghost_android_apply_render_scale(ANativeWindow *native_window)
{
  const uint32_t divisor = GHOST_android_render_scale_divisor();
  if (native_window == nullptr || divisor <= 1) {
    return;
  }
  const int32_t native_w = ANativeWindow_getWidth(native_window);
  const int32_t native_h = ANativeWindow_getHeight(native_window);
  if (native_w <= 0 || native_h <= 0) {
    return;
  }
  const int32_t w = std::max(1, native_w / int32_t(divisor));
  const int32_t h = std::max(1, native_h / int32_t(divisor));""",
"""static void ghost_android_apply_render_scale(ANativeWindow *native_window)
{
  if (native_window == nullptr) {
    return;
  }
  const int32_t native_w = ANativeWindow_getWidth(native_window);
  const int32_t native_h = ANativeWindow_getHeight(native_window);
  if (native_w <= 0 || native_h <= 0) {
    return;
  }
  const uint32_t divisor = GHOST_android_render_scale_divisor();
  if (GHOST_android_drnas_a810_enabled()) {
    int32_t aw, ah;
    GHOST_android_drnas_a810_size(native_w, native_h, aw, ah);
    const float touch_factor = float(aw) / float(native_w);
    if (ANativeWindow_setBuffersGeometry(native_window, aw, ah, 0) == 0) {
      GHOST_android_drnas_touch_ratio().store(touch_factor, std::memory_order_relaxed);
      __android_log_print(ANDROID_LOG_INFO, "DRNAS-A810",
                          "Adreno 810: %dx%d -> %dx%d (Vulkan only, ratio %.3f)",
                          native_w, native_h, aw, ah, touch_factor);
    }
    else {
      GHOST_android_drnas_touch_ratio().store(1.0f, std::memory_order_relaxed);
      __android_log_print(ANDROID_LOG_WARN, "DRNAS-A810",
                          "Failed to adjust Vulkan buffer geometry");
    }
    return;
  }
  if (divisor <= 1) {
    return;
  }
  const int32_t w = std::max(1, native_w / int32_t(divisor));
  const int32_t h = std::max(1, native_h / int32_t(divisor));""")
w = once(w, """  const int32_t w = native_window_ ? ANativeWindow_getWidth(native_window_) / int32_t(divisor) : 0;
  const int32_t h = native_window_ ? ANativeWindow_getHeight(native_window_) / int32_t(divisor) :
                                     0;
  bounds.set(0, 0, w, h);""",
"""  const int32_t native_w = native_window_ ? ANativeWindow_getWidth(native_window_) : 0;
  const int32_t native_h = native_window_ ? ANativeWindow_getHeight(native_window_) : 0;
  int32_t w = native_w / int32_t(divisor);
  int32_t h = native_h / int32_t(divisor);
  if (GHOST_android_drnas_a810_enabled()) {
    GHOST_android_drnas_a810_size(native_w, native_h, w, h);
  }
  bounds.set(0, 0, w, h);""")
win.write_text(w)

s = sys_file.read_text()
s = once(s, """    width = uint32_t(ANativeWindow_getWidth(app_->window)) / divisor;
    height = uint32_t(ANativeWindow_getHeight(app_->window)) / divisor;""",
"""    const int32_t native_w = ANativeWindow_getWidth(app_->window);
    const int32_t native_h = ANativeWindow_getHeight(app_->window);
    if (GHOST_android_drnas_a810_enabled()) {
      int32_t rw, rh;
      GHOST_android_drnas_a810_size(native_w, native_h, rw, rh);
      width = uint32_t(std::max(0, rw));
      height = uint32_t(std::max(0, rh));
    }
    else {
      width = uint32_t(native_w) / divisor;
      height = uint32_t(native_h) / divisor;
    }""")
sys_file.write_text(s)
print("PASS: A810 only Vulkan aspect-correct 960x544 budget and touch transform")
