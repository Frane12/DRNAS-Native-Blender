#!/usr/bin/env python3
"""Fix native Blender v8 edge-of-screen relative pointer and Android IME access.

Runs AFTER add_control_group_editor.py on the pinned upstream Java sources.
Only Java-side changes: keep proven native libblender.so and GPU drivers intact.
All anchors are checked to fail CI closed if upstream changes.
"""
from pathlib import Path
import sys

java = (Path(sys.argv[1]) /
        "build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java")
source = java.read_text(encoding="utf-8")


def once(old, new):
    global source
    found = source.count(old)
    if found != 1:
        raise RuntimeError(f"Expected exactly one matching Java anchor, got {found}: {old[:110]!r}")
    source = source.replace(old, new, 1)


# Android PopupWindow clips a 38dp cursor window to the available app frame by
# default. The hot spot could not VISUALLY reach the right and bottom edges even
# when the native pointer coordinate was already clamped correctly.
once(
    "      drnasPointerWindow.setTouchable(false);",
    """      drnasPointerWindow.setTouchable(false);
      // Render the cursor hotspot at the true edge. Let the icon extend outside
      // the app frame; Android will naturally crop off-screen pixels.
      drnasPointerWindow.setClippingEnabled(false);""",
)

# Trackpad is a separate full-screen popup; prefer its actually measured bounds
# over potentially smaller decor measurements when navigation/cutout layouts
# differ. Both native coordinates and visual hotspot use the same pixel space.
once(
    """    View decor = getWindow().getDecorView();
    drnasPointerX = Math.max(0, Math.min(decor.getWidth() - 1, x));
    drnasPointerY = Math.max(0, Math.min(decor.getHeight() - 1, y));""",
    """    View decor = getWindow().getDecorView();
    View bounds = (drnasMousePad != null && drnasMousePad.getWidth() > 0
        && drnasMousePad.getHeight() > 0) ? drnasMousePad : decor;
    drnasPointerX = Math.max(0, Math.min(Math.max(1, bounds.getWidth()) - 1, x));
    drnasPointerY = Math.max(0, Math.min(Math.max(1, bounds.getHeight()) - 1, y));""",
)

# Critical IME bug: INPUT_METHOD_NOT_NEEDED allows app popup windows to draw
# ABOVE the Android keyboard. The full-screen trackpad can then consume all
# keyboard taps. Declare that every overlay must remain BELOW the IME.
for var in ("drnasMouseWindow", "drnasPointerWindow", "popup", "drnasEditorPopup"):
    old = f"      {var}.setInputMethodMode(android.widget.PopupWindow.INPUT_METHOD_NOT_NEEDED);"
    if var == "popup":
        # DrnasPanel's setting is indented exactly six spaces as well.
        pass
    if var == "drnasEditorPopup":
        old = "    drnasEditorPopup.setInputMethodMode(android.widget.PopupWindow.INPUT_METHOD_NOT_NEEDED);"
    if var == "drnasPointerWindow":
        # Add explicit IME placement to the pointer popup (previously implicit).
        once(
            "      drnasPointerWindow.setClippingEnabled(false);",
            """      drnasPointerWindow.setClippingEnabled(false);
      drnasPointerWindow.setInputMethodMode(
          android.widget.PopupWindow.INPUT_METHOD_NEEDED);""",
        )
        continue
    once(old, old.replace("INPUT_METHOD_NOT_NEEDED", "INPUT_METHOD_NEEDED"))

# A hidden 1px text-editor view already has a real InputConnection and JNI
# nativeOnCommitText() in upstream Blender. On modern Android, opening the IME
# synchronously during a focus transition is sometimes silently ignored.
# Restart the connection after focus and request the keyboard on the next UI
# message. Do not synthesize characters into shortcuts: preserve Unicode JNI.
once(
    """  public void showKeyboard() {
    runOnUiThread(() -> {
      inputView.setFocusableInTouchMode(true);
      inputView.requestFocus();
      InputMethodManager imm = (InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE);
      imm.showSoftInput(inputView, InputMethodManager.SHOW_IMPLICIT);
    });
  }""",
    """  public void showKeyboard() {
    runOnUiThread(() -> {
      inputView.setFocusable(true);
      inputView.setFocusableInTouchMode(true);
      inputView.requestFocus();
      InputMethodManager imm = (InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE);
      if (imm == null) return;
      imm.restartInput(inputView);
      inputView.post(() -> {
        if (!isFinishing() && !isDestroyed() && inputView.isAttachedToWindow()) {
          inputView.requestFocus();
          imm.showSoftInput(inputView, InputMethodManager.SHOW_IMPLICIT);
        }
      });
    });
  }""",
)

# Many keyboards use the code-point deletion API and IME action instead of
# sending KEYCODE_DEL/ENTER through sendKeyEvent(). Use the already implemented
# native key bridge. Preserve existing composition and Unicode text forwarding.
once(
    """        @Override
        public boolean deleteSurroundingText(int beforeLength, int afterLength) {
          composing = "";
          for (int i = 0; i < beforeLength; i++) {
            nativeOnKey(KeyEvent.KEYCODE_DEL, KeyEvent.ACTION_DOWN, 0);
            nativeOnKey(KeyEvent.KEYCODE_DEL, KeyEvent.ACTION_UP, 0);
          }
          return true;
        }""",
    """        @Override
        public boolean deleteSurroundingText(int beforeLength, int afterLength) {
          composing = "";
          for (int i = 0; i < Math.min(128, Math.max(0, beforeLength)); i++) {
            nativeOnKey(KeyEvent.KEYCODE_DEL, KeyEvent.ACTION_DOWN, 0);
            nativeOnKey(KeyEvent.KEYCODE_DEL, KeyEvent.ACTION_UP, 0);
          }
          for (int i = 0; i < Math.min(128, Math.max(0, afterLength)); i++) {
            nativeOnKey(KeyEvent.KEYCODE_FORWARD_DEL, KeyEvent.ACTION_DOWN, 0);
            nativeOnKey(KeyEvent.KEYCODE_FORWARD_DEL, KeyEvent.ACTION_UP, 0);
          }
          return true;
        }

        @Override
        public boolean deleteSurroundingTextInCodePoints(int beforeLength, int afterLength) {
          return deleteSurroundingText(beforeLength, afterLength);
        }

        @Override
        public boolean performEditorAction(int actionCode) {
          nativeOnKey(KeyEvent.KEYCODE_ENTER, KeyEvent.ACTION_DOWN, 0);
          nativeOnKey(KeyEvent.KEYCODE_ENTER, KeyEvent.ACTION_UP, 0);
          return true;
        }""",
)

# Keep installed v8 untouched; install v9 side-by-side for user comparison.
# AndroidManifest versionName/label are handled in the same source-level
# manifest that the v8 workflow repack signs.
java.write_text(source, encoding="utf-8")

manifest = java.parents[4] / "AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
for old, new in (
    ("hr.drnas.blendernativecontrolstest2026v8", "hr.drnas.blendernativepointerimetest2026v9"),
    ("0.1.8-control-editor-test", "0.1.9-relative-ime-test"),
    ("Native Blender Controls v8 TEST", "Native Blender Pointer + IME v9 TEST"),
    ('android:versionCode="9"', 'android:versionCode="10"'),
):
    found = m.count(old)
    if found < 1 or (old != "Native Blender Controls v8 TEST" and found != 1):
        raise RuntimeError(f"Unexpected manifest anchor count {found}: {old!r}")
    m = m.replace(old, new)
manifest.write_text(m, encoding="utf-8")

assert "nativeOnCommitText(text.substring(common))" in source
assert "drnasPointerWindow.setClippingEnabled(false)" in source
assert "deleteSurroundingTextInCodePoints" in source
print("PASS: full-size pointer area, unclipped cursor, IME-safe overlays, Unicode input bridge and deletion/enter keys")
