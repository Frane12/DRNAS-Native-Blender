#!/usr/bin/env python3
"""Release-only patches for pinned upstream Android Blender Activity.

Applied AFTER the DRNAS controls, shortcut bar, splash and identity patches.
Keep the native Blender render path, but remove the automatic startup log,
the Log-path toast and add a real Android Back/gesture -> exit path.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
java_dir = root / "build_files/android/apk/app/src/main/java/org/blender/blender"
activity = java_dir / "BlenderActivity.java"
splash = java_dir / "DrnasSplashActivity.java"

def once(value, old, new):
    n = value.count(old)
    if n != 1:
        raise RuntimeError(f"Expected one anchor (found {n}): {old[:96]!r}")
    return value.replace(old, new, 1)

def between(value, first, last, replacement):
    if value.count(first) != 1 or value.count(last) != 1:
        raise RuntimeError(f"Changed pinned Java sources near {first[:60]!r}")
    a = value.index(first)
    b = value.index(last)
    if b <= a:
        raise RuntimeError("Invalid source order")
    return value[:a] + replacement + value[b:]

s = activity.read_text()
s = once(s, "    chooseLogPath();", "    configureDrnasRenderOutput();")
s = once(s, "    announceLogPath();\n", "")
s = once(s, "  private native void nativeSetLogPath(String path);\n", "")
s = once(s, "  private String logPath = null;\n", "")
s = between(
    s,
    "  /* Everything Blender prints is copied to this file",
    "  private void publishOutputDir(File parent) {",
    """  /* Keep render export working without creating any startup log file. */
  private void configureDrnasRenderOutput() {
    File[] candidates = {
        Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
        getExternalFilesDir(null),
        getFilesDir()
    };
    for (File parent : candidates) {
      if (parent == null) continue;
      File folder = new File(parent, "Blender");
      if (!folder.isDirectory() && !folder.mkdirs()) continue;
      File probe = new File(folder, ".drnas-write-probe");
      try (FileOutputStream out = new FileOutputStream(probe)) {
        out.write(0);
      }
      catch (Exception ignored) {
        continue;
      }
      finally {
        probe.delete();
      }
      publishOutputDir(parent);
      return;
    }
  }

""",
)
s = between(
    s, "  private void announceLogPath() {", "  private void extractRuntimeIfNeeded() {", ""
)

s = once(
    s,
    "    installDrnasShortcutStrip();",
    "    installDrnasShortcutStrip();\n    installDrnasAndroidBack();",
)

exit_methods = """  /* Android 13+ uses OnBackInvokedCallback; older navigation uses onBackPressed.
   * Either system back button or edge-swipe reaches the same confirmation. */
  private android.window.OnBackInvokedCallback drnasBackCallback;
  private boolean drnasExitDialogOpen = false;
  private boolean drnasExitRequested = false;

  private void installDrnasAndroidBack() {
    if (Build.VERSION.SDK_INT >= 33) {
      drnasBackCallback = () -> showDrnasExitDialog();
      getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
          android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, drnasBackCallback);
    }
  }

  @Override
  public void onBackPressed() {
    showDrnasExitDialog();
  }

  private void showDrnasExitDialog() {
    if (drnasExitDialogOpen || drnasExitRequested || isFinishing()) return;
    drnasExitDialogOpen = true;
    new android.app.AlertDialog.Builder(this)
        .setTitle("Exit Native Blender?")
        .setMessage("Unsaved Blender changes will be lost. Close the application?")
        .setNegativeButton("Stay", (dialog, which) -> {})
        .setPositiveButton("Exit", (dialog, which) -> exitDrnasBlender())
        .setOnDismissListener(dialog -> drnasExitDialogOpen = false)
        .show();
  }

  private void exitDrnasBlender() {
    if (drnasExitRequested) return;
    drnasExitRequested = true;
    /* Release held DRNAS mouse buttons before closing the native surface. */
    try {
      nativeOnDrnasInput(3, 0f, 0f, 0f);
      nativeOnDrnasInput(5, 0f, 0f, 0f);
    }
    catch (Throwable ignored) {}
    finishAndRemoveTask();
    /* NativeActivity can leave Blender's worker thread running after finish().
     * A deliberate confirmed exit must stop the whole dedicated APK process. */
    new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(
        () -> android.os.Process.killProcess(android.os.Process.myPid()), 220);
  }

  @Override
  protected void onDestroy() {
    if (Build.VERSION.SDK_INT >= 33 && drnasBackCallback != null) {
      getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(drnasBackCallback);
      drnasBackCallback = null;
    }
    super.onDestroy();
  }

"""
s = once(s, "  private void requestAllFilesAccess() {", exit_methods + "  private void requestAllFilesAccess() {")
if "announceLogPath()" in s or "blender-startup.log" in s or "nativeSetLogPath(" in s:
    raise RuntimeError("Startup log UI or file logging remains in Blender Activity")
activity.write_text(s)

t = splash.read_text()
splash_back = """    private android.window.OnBackInvokedCallback splashBackCallback;

    private void closeSetupScreen() {
        finishAndRemoveTask();
        /* Incomplete staging is safely discarded at the next launch. */
        handler.postDelayed(() -> android.os.Process.killProcess(
            android.os.Process.myPid()), 220);
    }

    @Override public void onBackPressed() {
        closeSetupScreen();
    }

"""
t = once(t, "    @Override public void onCreate(Bundle state) {", splash_back + "    @Override public void onCreate(Bundle state) {")
t = once(
    t,
    "        super.onCreate(state);",
    """        super.onCreate(state);
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            splashBackCallback = () -> closeSetupScreen();
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                splashBackCallback);
        }""",
)
t = once(
    t,
    "    @Override protected void onDestroy() {",
    """    @Override protected void onDestroy() {
        if (android.os.Build.VERSION.SDK_INT >= 33 && splashBackCallback != null) {
            getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(splashBackCallback);
            splashBackCallback = null;
        }""",
)
splash.write_text(t)
print("PASS: no visible/file startup log; Android back arrow/edge gesture closes Blender and setup with confirmation")
