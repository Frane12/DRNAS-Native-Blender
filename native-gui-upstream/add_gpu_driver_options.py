#!/usr/bin/env python3
"""Apply after all accepted v6 controls and original native patches, on pinned upstream."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).resolve().parent

def once(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old))
    return s.replace(old,new,1)
java=root/'build_files/android/apk/app/src/main/java/org/blender/blender'
p=java/'BlenderActivity.java';s=p.read_text()
s=once(s,'    DrnasGpuProfile.apply(this);','    DrnasGpuProfile.apply(this);\n    DrnasGpuOptions.apply(this);')
s=once(s,'    super.onCreate(state);','    super.onCreate(state);\n    DrnasGpuOptions.watch(this);')
s=once(s,'    installDrnasMouseOptions(optionRows);','    DrnasGpuOptions.install(this, optionRows);\n    installDrnasMouseOptions(optionRows);')
p.write_text(s)
p=java/'DrnasGpuProfile.java';s=p.read_text()
s=once(s,'  private DrnasGpuProfile() {}','  public static String renderer = "unavailable";\n  private DrnasGpuProfile() {}')
s=once(s,'    String gpu = queryGlesRenderer();','    String gpu = queryGlesRenderer();\n    renderer = gpu;')
p.write_text(s)
for name in ('DrnasGpuPolicy.java','DrnasGpuOptions.java'):(java/name).write_text((here/name).read_text())

# Generalize the accepted A810 aspect-fit path to user-selected caps on every GPU.
p=root/'intern/ghost/intern/GHOST_AndroidMemoryTier.hh';s=p.read_text()
s=once(s,'  return flag && flag[0] == \'1\' && flag[1] == \'\\0\';', '''  const char *override = getenv("DRNAS_RENDER_OVERRIDE");
  return (override && override[0] == '1') || (flag && flag[0] == '1' && flag[1] == '\\0');''')
s=once(s,'  const float factor = std::min(1.0f,\n                                std::min(960.0f / float(native_w),\n                                         544.0f / float(native_h)));', '''  const char *override = getenv("DRNAS_RENDER_OVERRIDE");
  int cap_w = 960, cap_h = 544;
  if (override && override[0] == '1') {
    const char *rw = getenv("DRNAS_RENDER_WIDTH"), *rh = getenv("DRNAS_RENDER_HEIGHT");
    cap_w = rw ? atoi(rw) : 0;
    cap_h = rh ? atoi(rh) : 0;
    if (cap_w <= 0 || cap_h <= 0) return; /* Explicit native resolution. */
    cap_w = std::min(cap_w, 8192); cap_h = std::min(cap_h, 8192);
  }
  if (native_w < native_h) std::swap(cap_w, cap_h);
  const double factor = std::min(1.0,
                                std::min(double(cap_w) / native_w,
                                         double(cap_h) / native_h));''')
# X and Y differ slightly due to even-pixel rounding; do not share one ratio.
s=once(s,'inline std::atomic<float> &GHOST_android_drnas_touch_ratio()', 'inline std::atomic<float> &GHOST_android_drnas_touch_ratio_x()')
a=s.index('/** Divisor applied to the native window size.')
s=s[:a]+'''inline std::atomic<float> &GHOST_android_drnas_touch_ratio_y()
{
  static std::atomic<float> ratio{1.0f};
  return ratio;
}

'''+s[a:]
s=s.replace('GHOST_android_drnas_touch_ratio().load','GHOST_android_drnas_touch_ratio_x().load')
s=once(s,'inline float ghost_android_scale_input(float value)','inline float ghost_android_scale_input_x(float value)')
a=s.index('inline float ghost_android_scale_input_x(');b=s.index('\n}\n',a)+3
func=s[a:b].replace('scale_input_x','scale_input_y').replace('touch_ratio_x','touch_ratio_y')
s=s[:b]+'\n'+func+s[b:];p.write_text(s)
p=root/'intern/ghost/intern/GHOST_WindowAndroid.cc';s=p.read_text()
s=s.replace('GHOST_android_drnas_touch_ratio().store','GHOST_android_drnas_touch_ratio_x().store')
s=once(s,'      GHOST_android_drnas_touch_ratio_x().store(touch_factor, std::memory_order_relaxed);','''      GHOST_android_drnas_touch_ratio_x().store(touch_factor, std::memory_order_relaxed);
      GHOST_android_drnas_touch_ratio_y().store(float(ah) / float(native_h), std::memory_order_relaxed);''')
s=once(s,'      GHOST_android_drnas_touch_ratio_x().store(1.0f, std::memory_order_relaxed);','''      GHOST_android_drnas_touch_ratio_x().store(1.0f, std::memory_order_relaxed);
      GHOST_android_drnas_touch_ratio_y().store(1.0f, std::memory_order_relaxed);''')
s=s.replace('"DRNAS-A810"','"DRNAS-GPU"').replace('"Adreno 810: %dx%d','"Render: %dx%d');p.write_text(s)
p=root/'intern/ghost/intern/GHOST_SystemAndroid.cc';s=p.read_text()
s=s.replace('ghost_android_scale_input(AMotionEvent_getX','ghost_android_scale_input_x(AMotionEvent_getX').replace('ghost_android_scale_input(AMotionEvent_getY','ghost_android_scale_input_y(AMotionEvent_getY')
s=s.replace('ghost_android_scale_input(event.x)','ghost_android_scale_input_x(event.x)').replace('ghost_android_scale_input(event.y)','ghost_android_scale_input_y(event.y)')
assert 'ghost_android_scale_input(' not in s;p.write_text(s)

# Keep Android's Vulkan loader and WSI; replace only the ICD through adrenotools.
p=root/'source/blender/gpu/vulkan/vk_backend.cc';s=p.read_text()
a=s.index('  const char *driver_dir = native_lib_dir.c_str();');b=s.index('  void *libvulkan = adrenotools_open_libvulkan(',a)
s=s[:a]+'''  const char *driver_dir = native_lib_dir.c_str();
  const char *driver_name = getenv("DRNAS_GPU_DRIVER");
  if (driver_name == nullptr || strncmp(driver_name, "libdrnas_gpu_", 13) != 0 ||
      strchr(driver_name, '/') != nullptr || strchr(driver_name, '\\\\') != nullptr) {
    return false; /* System driver is the default, even though APK carries ten ICDs. */
  }
  const std::string driver_path = native_lib_dir + driver_name;
  if (access(driver_path.c_str(), R_OK) != 0) return false;
  const char *kind = getenv("DRNAS_GPU_KIND");
  if (kind && strcmp(kind, "turnip") == 0) {
    /* Conservative upstream workaround; do not apply Turnip flags to PanVK. */
    setenv("TU_DEBUG", "sysmem", 1);
  }

'''+s[b:];s=s.replace('#  include <cstdlib>','#  include <cstdlib>\n#  include <cstring>');p.write_text(s)
# Only a successfully presented frame clears Java's boot-failure latch.
p=root/'intern/ghost/intern/GHOST_ContextVK.cc';s=p.read_text()
anchor='  acquired_swapchain_image_index_.reset();\n\n  /* SUBOPTIMAL presented correctly'
s=once(s,anchor,'''  acquired_swapchain_image_index_.reset();
#ifdef __ANDROID__
  if (present_result == VK_SUCCESS || present_result == VK_SUBOPTIMAL_KHR) {
    static bool drnas_frame_announced = false;
    if (!drnas_frame_announced) {
      const char *path = getenv("DRNAS_GPU_READY_FILE");
      if (path) {
        if (FILE *ready = fopen(path, "w")) {
          fputs("PRESENTED\\n", ready);
          fclose(ready);
          drnas_frame_announced = true;
        }
      }
    }
  }
#endif

  /* SUBOPTIMAL presented correctly''');p.write_text(s)

# Compile every accepted GUI helper in native builds, not only in the repack workflow.
p=root/'build_files/android/apk/package.sh';s=p.read_text()
a=s.index('"$JAVA_HOME/bin/javac"');b=s.index('\n"$BT/d8"',a)
s=s[:a]+'''"$JAVA_HOME/bin/javac" -classpath "$ANDROID_JAR" -source 17 -target 17 \\
  -d "$STAGE/javac" "$SCRIPT_DIR"/app/src/main/java/org/blender/blender/*.java'''+s[b:]
anchor='# The Python interpreter, shipped so sys.executable is real.'
s=once(s,anchor,'''# Bundle the pinned EMU driver set with notices in an executable APK location.
python3 "$DRNAS_PATCH_ROOT/package_gpu_drivers.py" "$DRNAS_GPU_CACHE" "$JNI" "$ASSETS"
rm -f "$JNI/libvulkan_turnip.so"

'''+anchor)
# ASSETS is assigned later upstream, so use deterministic stage path here.
s=s.replace('"$DRNAS_GPU_CACHE" "$JNI" "$ASSETS"','"$DRNAS_GPU_CACHE" "$JNI" "$STAGE/assets"')
# Add Python zoom/save helpers before payload ZIP is built.
s=once(s,'echo "[apk] runtime payload:', 'python3 "$DRNAS_PATCH_ROOT/package_smooth_zoom_runtime.py" "$ASSETS/blender_runtime.zip"\necho "[apk] runtime payload:')
p.write_text(s)
print('PASS: GPU-gated ICD selection, native aspect caps with XY touch, first-present recovery, v6 runtime')
# Persistent ccache applies to both host generators and Android C/C++; cap peak RAM.
p=root/'build_files/android/build_apk.sh';s=p.read_text()
s=once(s,'-DWITH_HEADLESS=ON -DWITH_X11_XINPUT=OFF','-DWITH_COMPILER_CCACHE=ON -DWITH_HEADLESS=ON -DWITH_X11_XINPUT=OFF')
s=once(s,'-DBLENDER_ANDROID_CONFIG="$CONFIG" "${ADRENOTOOLS_ARGS[@]}"','-DWITH_COMPILER_CCACHE=ON -DBLENDER_ANDROID_CONFIG="$CONFIG" "${ADRENOTOOLS_ARGS[@]}"')
s=s.replace('ninja -C "$HOST"','ninja -j2 -C "$HOST"').replace('ninja -C "$BUILD"','ninja -j2 -C "$BUILD"')
p.write_text(s)
