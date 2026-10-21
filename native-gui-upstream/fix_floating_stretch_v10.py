#!/usr/bin/env python3
"""V10: align relative mouse coordinates across Android edge-to-edge stretches
and turn existing mouse/keyboard popups into compact, collapsible utility windows.

Applied after v9 on the pinned Java source. Does NOT modify libblender.so.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
path=root/'build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java'
source=path.read_text()

def once(old,new):
    global source
    count=source.count(old)
    if count != 1: raise RuntimeError(f"Expected one v9 anchor; got {count}: {old[:120]!r}")
    source=source.replace(old,new,1)

# IMPORTANT: the Android PopupWindow receiving gestures can have a different
# measured extent from NativeActivity's decor viewport when an app toggles
# edge-to-edge, immersive navigation, or an IME. Relative deltas are accumulated
# in popup coordinates, but GHOST must get physical native viewport pixels.
# Keep the pointer in touchpad coordinates and map BOTH the cursor overlay and
# the JNI cursor-move into the same decor-relative system.
once("  private void drnasMovePointer(float x, float y) {",
"""  private float drnasNativePointerX(float x) {
    final View decor=getWindow().getDecorView();
    final int viewport=Math.max(1,decor.getWidth());
    final int touch=drnasMousePad==null ? viewport : Math.max(1,drnasMousePad.getWidth());
    return Math.max(0f, Math.min(viewport-1f, x * ((viewport-1f) / Math.max(1f,touch-1f))));
  }
  private float drnasNativePointerY(float y) {
    final View decor=getWindow().getDecorView();
    final int viewport=Math.max(1,decor.getHeight());
    final int touch=drnasMousePad==null ? viewport : Math.max(1,drnasMousePad.getHeight());
    return Math.max(0f, Math.min(viewport-1f, y * ((viewport-1f) / Math.max(1f,touch-1f))));
  }
  private void drnasMovePointer(float x, float y) {""")
once("    drnasSendInput(1, drnasPointerX, drnasPointerY, 0);",
     "    drnasSendInput(1, drnasNativePointerX(drnasPointerX), drnasNativePointerY(drnasPointerY), 0);")
once("      int x = Math.round(drnasPointerX) - dpDrnas(4 * drnasCursorPercent / 100f), y = Math.round(drnasPointerY) - dpDrnas(4 * drnasCursorPercent / 100f);",
"""      // PopupWindow positioning is screen-based. Account for the app decor
      // origin (status/navigation/cutout inset) just as for native coordinates.
      int[] decorOnScreen = new int[2];
      getWindow().getDecorView().getLocationOnScreen(decorOnScreen);
      int x = decorOnScreen[0] + Math.round(drnasNativePointerX(drnasPointerX))
          - dpDrnas(4 * drnasCursorPercent / 100f);
      int y = decorOnScreen[1] + Math.round(drnasNativePointerY(drnasPointerY))
          - dpDrnas(4 * drnasCursorPercent / 100f);""")

# When the user changes Stretch, a rotation or the Android IME changes window
# insets, refresh movable popups and virtual cursor in the following frame.
once("    drnasAttachGear(drnasMouseDock, true);",
"""    drnasAttachGear(drnasMouseDock, true);
    drnasInstallCompactWindows();
    final View viewport=getWindow().getDecorView();
    viewport.addOnLayoutChangeListener((v,newLeft,newTop,newRight,newBottom,oldLeft,oldTop,oldRight,oldBottom)->{
      if ((newRight-newLeft)==(oldRight-oldLeft) && (newBottom-newTop)==(oldBottom-oldTop)) return;
      v.post(()->{
        if (isFinishing()||isDestroyed()) return;
        drnasRefreshPanels();
        if (drnasRelativeMouse) drnasRefreshMouseLayer();
        drnasUpdatePointer();
      });
    });""")

# Mini-window presentation: the existing independent draggable DrnasPanel is
# reused; no second overlay / new touch windows. The mouse dock's children can
# collapse down to a compact 2-button header, revealing Open/Save dialog rows.
# Shortcut strip already has its own opener, gear and drag grip.
once("  private void requestAllFilesAccess() {",
"""  private java.util.ArrayList<View> drnasDockWindowChildren;
  private TextView drnasDockMinimize;

  private void drnasCompactMouseWindow(boolean collapsed) {
    if (drnasDockWindowChildren==null || drnasDockMinimize==null) return;
    // Avoid a stuck LMB/RMB (including the double-tap hold state) when hiding.
    if (collapsed) {
      drnasStopSpringZoom();
      drnasReleaseAllInputs();
    }
    for (View child:drnasDockWindowChildren) {
      child.setVisibility(collapsed ? View.GONE:View.VISIBLE);
    }
    drnasDockMinimize.setText(collapsed ? "▣" : "▾");
    drnasDockMinimize.setContentDescription(collapsed ?
        "Otvori plutajući prozor miša" : "Smanji prozor miša");
    drnasPrefs.edit().putBoolean("mouse_window_minimized",collapsed).apply();
    drnasMouseDock.requestLayout();
    drnasRefreshPanels();
  }

  private void drnasInstallCompactWindows() {
    if (drnasMouseDock==null || drnasKeyStrip==null) return;
    final LinearLayout mouseDock=(LinearLayout)drnasMouseDock;
    // Rounded, clearly delineated, independent mini utility windows.
    android.graphics.drawable.GradientDrawable mouseBg=drnasPill(Color.argb(225,16,34,52));
    mouseBg.setStroke(dpDrnas(1),Color.argb(218,111,177,207));
    drnasMouseDock.setBackground(mouseBg);
    android.graphics.drawable.GradientDrawable keysBg=drnasPill(Color.argb(229,17,35,53));
    keysBg.setStroke(dpDrnas(1),Color.argb(200,92,158,193));
    drnasKeyStrip.setBackground(keysBg);
    drnasDockWindowChildren=new java.util.ArrayList<>();
    // Keep original drag grip visible even when the dock is collapsed.
    for (int i=1;i<mouseDock.getChildCount();i++)
      drnasDockWindowChildren.add(mouseDock.getChildAt(i));
    drnasDockGrip.setContentDescription("Drži i pomakni prozor miša");
    drnasDockMinimize=drnasUiLabel("▾");
    drnasDockMinimize.setTextSize(18);
    drnasDockMinimize.setGravity(Gravity.CENTER);
    drnasDockMinimize.setContentDescription("Smanji prozor miša");
    drnasDockMinimize.setBackground(drnasPill(Color.argb(220,43,73,97)));
    mouseDock.addView(drnasDockMinimize,
        new LinearLayout.LayoutParams(dpDrnas(32),dpDrnas(48)));
    drnasDockMinimize.setOnClickListener(v->drnasCompactMouseWindow(
        !drnasPrefs.getBoolean("mouse_window_minimized",false)));
    if (drnasPrefs.getBoolean("mouse_window_minimized",false))
      drnasCompactMouseWindow(true);
    drnasRefreshPanels();
  }

  private void requestAllFilesAccess() {""")

# Strictly separate test package, no accidental overwrite of v9.
path.write_text(source)
manifest=root/'build_files/android/apk/app/src/main/AndroidManifest.xml'
m=manifest.read_text()
for old,new in (
 ("hr.drnas.blendernativepointerimetest2026v9","hr.drnas.blendernativefloatingstretcht2026v10"),
 ("0.1.9-relative-ime-test","0.1.10-floating-stretch-test"),
 ("Native Blender Pointer + IME v9 TEST","Native Blender Floating Windows v10 TEST"),
 ('android:versionCode="10"','android:versionCode="11"'),
):
    n=m.count(old)
    if not n:raise RuntimeError(f"Missing Android manifest identity: {old!r}")
    if old != "Native Blender Pointer + IME v9 TEST" and n!=1:
        raise RuntimeError(f"Unexpected {n} copies of {old!r}")
    m=m.replace(old,new)
manifest.write_text(m)
assert "drnasNativePointerX" in source and "mouse_window_minimized" in source
print("PASS: v10 popup/decor stretched pointer mapping, IME retention, collapsible draggable mouse/key utility windows; native untouched")
