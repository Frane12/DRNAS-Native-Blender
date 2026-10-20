#!/usr/bin/env python3
"""Assemble isolated, clearly attributed DRNAS UI overlay on upstream Android Blender.

This builds *against* the native Blender Android GUI binary from the pinned
simfeo/blender android-alpha-4 APK. It does NOT rebuild/modify libblender.so,
nor does it use the previous DRNAS headless ELF.
"""
from __future__ import annotations

import pathlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: create_sdl3_gui_preview.py <upstream-apk-gradle-root>")
root = pathlib.Path(sys.argv[1]).resolve()
app = root / "app"
activity = app / "src/main/java/org/blender/blender/BlenderActivity.java"
manifest = app / "src/main/AndroidManifest.xml"
build = app / "build.gradle"

original = activity.read_text()
anchor = "    addContentView(inputView, new ViewGroup.LayoutParams(1, 1));"
assert original.count(anchor) == 1, "Pinned upstream Activity has changed; inspect before patching"
assert "private native void nativeOnKey(int keycode, int action, int metaState);" in original, "No proven JNI key bridge"
assert "private void requestAllFilesAccess()" in original

imports = """import android.graphics.Color;
import android.view.Gravity;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
"""
original = original.replace("import android.app.NativeActivity;", "import android.app.NativeActivity;\n" + imports, 1)
original = original.replace(anchor, anchor + "\n    installDrnasOverlay();", 1)

methods = """
  /*
   * Experimental DRNAS overlay over the REAL upstream Blender native viewport.
   * Keyboard-only shortcuts are routed through upstream's existing JNI key
   * bridge (GHOST_SystemAndroid::handleJavaKeyEvent). No fake mouse events.
   *
   * Keep the parent surface untouched: everything beyond the toolbar remains
   * handled by Blender's NativeActivity / GHOST input queue.
   */
  private void installDrnasOverlay() {
    final LinearLayout bar = new LinearLayout(this);
    bar.setOrientation(LinearLayout.HORIZONTAL);
    bar.setGravity(Gravity.CENTER_VERTICAL);
    bar.setBackgroundColor(Color.argb(215, 17, 35, 52));
    bar.setPadding(dpDrnas(4), dpDrnas(3), dpDrnas(4), dpDrnas(3));

    final LinearLayout commands = new LinearLayout(this);
    commands.setOrientation(LinearLayout.HORIZONTAL);
    addDrnasCommand(commands, "G", KeyEvent.KEYCODE_G);
    addDrnasCommand(commands, "R", KeyEvent.KEYCODE_R);
    addDrnasCommand(commands, "S", KeyEvent.KEYCODE_S);
    addDrnasCommand(commands, "ESC", KeyEvent.KEYCODE_ESCAPE);
    commands.setVisibility(View.GONE);

    final Button toggle = new Button(this);
    toggle.setText("DRNAS ◀");
    toggle.setAllCaps(false);
    toggle.setTextSize(11);
    toggle.setMinWidth(0);
    toggle.setMinimumWidth(0);
    toggle.setPadding(dpDrnas(4), 0, dpDrnas(4), 0);
    toggle.setOnClickListener(v -> {
      boolean showing = commands.getVisibility() != View.VISIBLE;
      commands.setVisibility(showing ? View.VISIBLE : View.GONE);
      toggle.setText(showing ? "DRNAS ▼" : "DRNAS ◀");
    });

    bar.addView(commands);
    bar.addView(toggle);
    FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
        ViewGroup.LayoutParams.WRAP_CONTENT, dpDrnas(52), Gravity.TOP | Gravity.RIGHT);
    params.setMargins(dpDrnas(6), dpDrnas(6), dpDrnas(8), 0);
    addContentView(bar, params);
  }

  private int dpDrnas(float value) {
    return Math.round(value * getResources().getDisplayMetrics().density);
  }

  private void addDrnasCommand(LinearLayout row, String label, int androidKey) {
    Button button = new Button(this);
    button.setText(label);
    button.setAllCaps(false);
    button.setTextSize(12);
    button.setMinWidth(0);
    button.setMinimumWidth(0);
    button.setPadding(0, 0, 0, 0);
    row.addView(button, new LinearLayout.LayoutParams(dpDrnas(50), dpDrnas(44)));
    button.setOnClickListener(v -> {
      nativeOnKey(androidKey, KeyEvent.ACTION_DOWN, 0);
      nativeOnKey(androidKey, KeyEvent.ACTION_UP, 0);
    });
  }

"""
original = original.replace("  private void requestAllFilesAccess() {", methods + "  private void requestAllFilesAccess() {", 1)
activity.write_text(original)

m = manifest.read_text()
assert 'android:label="Blender"' in m
m = m.replace('android:label="Blender"', 'android:label="DRNAS Native GUI (Upstream LAB)"')
manifest.write_text(m)

g = build.read_text()
assert "applicationId 'org.blender.blender'" in g, "Upstream applicationId has changed"
assert re.search(r"^def stageDir = .*", g, flags=re.MULTILINE), "Upstream stageDir has changed"
g = g.replace("applicationId 'org.blender.blender'", "applicationId 'hr.drnas.nativeblendergui'")
g = g.replace("versionName '5.3-android'", "versionName '0.1-gui-upstream-lab'")
g = re.sub(r"^def stageDir = .*", 'def stageDir = "${rootDir}/ci-stage"',
           g, count=1, flags=re.MULTILINE)
build.write_text(g)
print("DRNAS Native GUI preview overlay: Java/manifest/Gradle patch applied")
