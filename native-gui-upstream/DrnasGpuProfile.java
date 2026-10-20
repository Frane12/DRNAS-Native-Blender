/*
 * DRNAS native Blender GPU-specific startup profile.
 * GPU family detection is precise: Adreno 810, not a phone-model guess,
 * not Snapdragon 810 (whose GPU was Adreno 430).
 *
 * A temporary 1x1 GLES pbuffer is used to read the actual renderer BEFORE
 * Blender's Vulkan NativeActivity creates a swapchain. All GLES resources
 * are immediately released; the app itself continues using Vulkan only.
 */
package org.blender.blender;

import android.app.Activity;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES20;
import android.system.Os;
import android.util.Log;
import java.util.Locale;

public final class DrnasGpuProfile {
  private static final String TAG = "DRNAS-A810";
  private DrnasGpuProfile() {}

  public static boolean isAdreno810Renderer(String renderer) {
    if (renderer == null) return false;
    return renderer.matches("(?i).*\\badreno\\b[^0-9]*\\b810\\b.*");
  }

  /* Called by BlenderActivity before super.onCreate() starts native Vulkan. */
  public static void apply(Activity activity) {
    String gpu = queryGlesRenderer();
    boolean a810 = isAdreno810Renderer(gpu);
    try {
      Os.setenv("DRNAS_A810_RENDER_LIMIT", a810 ? "1" : "0", true);
    } catch (Exception exception) {
      Log.w(TAG, "Could not select GPU-specific Vulkan profile", exception);
    }
    if (a810) {
      Log.i(TAG, "GPU=" + gpu + "; enable Vulkan buffer <=960x544; "
                     + "do not change physical display resolution");
    } else {
      Log.i(TAG, "GPU=" + gpu + "; default Vulkan profile (A840 unchanged)");
    }
  }

  private static String queryGlesRenderer() {
    EGLDisplay display = EGL14.EGL_NO_DISPLAY;
    EGLContext context = EGL14.EGL_NO_CONTEXT;
    EGLSurface surface = EGL14.EGL_NO_SURFACE;
    try {
      display = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
      if (display == EGL14.EGL_NO_DISPLAY) return "unavailable";
      if (!EGL14.eglInitialize(display, new int[2], 0, new int[2], 0))
        return "unavailable";
      int[] attributes = {
          EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT,
          EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
          EGL14.EGL_NONE
      };
      EGLConfig[] configs = new EGLConfig[1];
      int[] count = new int[1];
      if (!EGL14.eglChooseConfig(display, attributes, 0, configs, 0, 1, count, 0)
          || count[0] == 0) return "unavailable";
      int[] buffer = {EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE};
      surface = EGL14.eglCreatePbufferSurface(display, configs[0], buffer, 0);
      if (surface == EGL14.EGL_NO_SURFACE) return "unavailable";
      int[] contextAttributes = {EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE};
      context = EGL14.eglCreateContext(display, configs[0], EGL14.EGL_NO_CONTEXT,
                                      contextAttributes, 0);
      if (context == EGL14.EGL_NO_CONTEXT) return "unavailable";
      if (!EGL14.eglMakeCurrent(display, surface, surface, context)) return "unavailable";
      String renderer = GLES20.glGetString(GLES20.GL_RENDERER);
      return renderer == null ? "unavailable" : renderer.trim();
    } catch (RuntimeException error) {
      Log.w(TAG, "Cannot query GL renderer; retaining default Vulkan profile", error);
      return "unavailable";
    } finally {
      if (display != EGL14.EGL_NO_DISPLAY) {
        EGL14.eglMakeCurrent(display, EGL14.EGL_NO_SURFACE,
                             EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT);
        if (context != EGL14.EGL_NO_CONTEXT) EGL14.eglDestroyContext(display, context);
        if (surface != EGL14.EGL_NO_SURFACE) EGL14.eglDestroySurface(display, surface);
        EGL14.eglTerminate(display);
      }
    }
  }
}
