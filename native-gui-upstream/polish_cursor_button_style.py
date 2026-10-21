#!/usr/bin/env python3
"""Visual-only polish over the device-validated v4 controls and spring behavior."""
from pathlib import Path
import sys

p = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java'
s = p.read_text()

def once(old, new):
    global s
    assert s.count(old) == 1, (old[:110], s.count(old))
    s = s.replace(old, new, 1)

once('  private boolean drnasRelativeMouse, drnasPointerEffect = true;',
     '  private boolean drnasRelativeMouse, drnasPointerEffect = true;\n  private int drnasCursorPercent = 70;')
once('    drnasMouseSpeed = drnasPrefs.getInt("mouse_speed", 100) / 100f;', '''    drnasMouseSpeed = drnasPrefs.getInt("mouse_speed", 100) / 100f;
    drnasCursorPercent = Math.max(40, Math.min(150, drnasPrefs.getInt("cursor_percent", 70)));''')
once('    options.addView(drnasUiLabel("Miš: tap = lijevi klik • 2 prsta = zoom / desni tap"));', '''    final TextView cursorSizeLabel = drnasUiLabel("Veličina kursora: " + drnasCursorPercent + "%");
    options.addView(cursorSizeLabel);
    SeekBar cursorSize = new SeekBar(this);
    cursorSize.setContentDescription("Veličina kursora od 40 do 150 posto");
    cursorSize.setMax(110); cursorSize.setProgress(drnasCursorPercent - 40);
    options.addView(cursorSize, new LinearLayout.LayoutParams(-1, dpDrnas(40)));
    cursorSize.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar b, int value, boolean user) {
        drnasCursorPercent = value + 40;
        cursorSizeLabel.setText("Veličina kursora: " + drnasCursorPercent + "%");
        if (user) drnasPrefs.edit().putInt("cursor_percent", drnasCursorPercent).apply();
        drnasUpdatePointer();
      }
      public void onStartTrackingTouch(SeekBar b) {}
      public void onStopTrackingTouch(SeekBar b) {}
    });
    options.addView(drnasUiLabel("Miš: tap = lijevi klik • 2 prsta = zoom / desni tap"));''')
once('new android.widget.PopupWindow(drnasPointer, dpDrnas(38), dpDrnas(38), false)',
     'new android.widget.PopupWindow(drnasPointer, dpDrnas(38 * drnasCursorPercent / 100f), dpDrnas(38 * drnasCursorPercent / 100f), false)')
once('int x = Math.round(drnasPointerX) - dpDrnas(4), y = Math.round(drnasPointerY) - dpDrnas(4);',
     'int x = Math.round(drnasPointerX) - dpDrnas(4 * drnasCursorPercent / 100f), y = Math.round(drnasPointerY) - dpDrnas(4 * drnasCursorPercent / 100f);')
once('      else drnasPointerWindow.update(x, y, -1, -1);', '''      else drnasPointerWindow.update(x, y, dpDrnas(38 * drnasCursorPercent / 100f), dpDrnas(38 * drnasCursorPercent / 100f));''')
once('''      if (!drnasPointerWindow.isShowing())
        drnasPointerWindow.showAtLocation(getWindow().getDecorView(), Gravity.TOP | Gravity.LEFT, x, y);''', '''      if (!drnasPointerWindow.isShowing()) {
        drnasPointerWindow.setWidth(dpDrnas(38 * drnasCursorPercent / 100f));
        drnasPointerWindow.setHeight(dpDrnas(38 * drnasCursorPercent / 100f));
        drnasPointerWindow.showAtLocation(getWindow().getDecorView(), Gravity.TOP | Gravity.LEFT, x, y);
      }''')

a = s.index('  private final class DrnasPointer extends View {')
b = s.index('\n  private ', a + len('  private final class DrnasPointer extends View {'))
# The existing nested class is followed by the smooth-zoom fields/methods.
old = s[a:b]
assert old.rstrip().endswith('  }'), old[-200:]
s = s[:a] + Path(__file__).with_name('drnas_refined_pointer.java.inc').read_text() + s[b:]

once('    button.setBackgroundColor(Color.argb(218, 24, 58, 86));', '    drnasStyleKey(button, true);')
once('        v.setAlpha(0.58f);', '        v.setPressed(true); v.setActivated(true);')
once('        v.setAlpha(1f);', '        v.setPressed(false); v.setActivated(false);')
once('dock.addView(button, new LinearLayout.LayoutParams(dpDrnas(56), dpDrnas(48)));', '''LinearLayout.LayoutParams mouseSize = new LinearLayout.LayoutParams(dpDrnas(68), dpDrnas(54));
      mouseSize.setMargins(dpDrnas(5), dpDrnas(4), dpDrnas(5), dpDrnas(4));
      dock.addView(button, mouseSize);''')
once('      lp.width = dpDrnas(56 * factor);', '      lp.width = dpDrnas(68 * factor);')
once('      lp.height = dpDrnas(48 * factor);', '''      lp.height = dpDrnas(54 * factor);
      if (lp instanceof ViewGroup.MarginLayoutParams) ((ViewGroup.MarginLayoutParams)lp)
          .setMargins(dpDrnas(5 * factor), dpDrnas(4), dpDrnas(5 * factor), dpDrnas(4));''')
once('      v.setTextSize(13f * factor);', '      v.setTextSize(14f * factor);')

once('''    button.setBackground(new android.graphics.drawable.RippleDrawable(
        android.content.res.ColorStateList.valueOf(Color.argb(95, 120, 220, 232)),
        drnasPill(Color.argb(155, 35, 50, 71)), null));''', '    drnasStyleKey(button, false);')
once('''    button.setBackground(drnasPill(enabled ? Color.rgb(35, 120, 137) :
                                          Color.rgb(29, 54, 79)));''', '    button.setActivated(enabled);')
once('    opener.setBackground(drnasPill(Color.rgb(37, 82, 114)));', '    drnasStyleKey(opener, false);')
once('    settings.setBackground(drnasPill(Color.rgb(37, 82, 114)));', '    drnasStyleKey(settings, false);')
once('    closeOptions.setAllCaps(false);', '    closeOptions.setAllCaps(false);\n    drnasStyleKey(closeOptions, false);')
once('    gestureSettings.setText("Osjetljivost gesta");',
     '    gestureSettings.setText("Osjetljivost gesta");\n    drnasStyleKey(gestureSettings, false);')
once('    background.setCornerRadius(dpDrnas(9));', '    background.setCornerRadius(dpDrnas(18));')
once('background.setStroke(dpDrnas(1), Color.argb(155, 67, 119, 169));',
     'background.setStroke(dpDrnas(1), Color.argb(100, 100, 169, 190));')

# Hiding zoom stops the spring and remeasures the shared dock. LMB/RMB retain
# their listeners and their common split-touch window from the proven v4.
once('    group.addView(zoom, new LinearLayout.LayoutParams(dpDrnas(170), dpDrnas(43)));', '''    final Button zoomToggle = new Button(this);
    final boolean visibleZoom = drnasPrefs.getBoolean("zoom_visible", true);
    zoomToggle.setText(visibleZoom ? "ZOOM ▾" : "ZOOM ▸");
    drnasStyleKey(zoomToggle, false);
    zoomToggle.setTextSize(11f);
    zoomToggle.setContentDescription("Prikaži ili sakrij zoom slider");
    LinearLayout.LayoutParams toggleSize = new LinearLayout.LayoutParams(dpDrnas(74), dpDrnas(48));
    toggleSize.setMargins(dpDrnas(4), 0, dpDrnas(4), 0);
    group.addView(zoomToggle, toggleSize);
    zoom.setVisibility(visibleZoom ? View.VISIBLE : View.GONE);
    zoom.setProgressTintList(android.content.res.ColorStateList.valueOf(Color.rgb(96, 207, 220)));
    zoom.setThumbTintList(android.content.res.ColorStateList.valueOf(Color.rgb(183, 242, 246)));
    group.addView(zoom, new LinearLayout.LayoutParams(dpDrnas(120), dpDrnas(48)));
    zoomToggle.setOnClickListener(v -> {
      drnasStopSpringZoom(); zoom.setProgress(50);
      boolean show = zoom.getVisibility() != View.VISIBLE;
      zoom.setVisibility(show ? View.VISIBLE : View.GONE);
      zoomToggle.setText(show ? "ZOOM ▾" : "ZOOM ▸");
      drnasPrefs.edit().putBoolean("zoom_visible", show).apply();
      drnasRefreshPanels();
    });''')
once('  private void requestAllFilesAccess() {', Path(__file__).with_name('drnas_button_skin.java.inc').read_text() + '\n  private void requestAllFilesAccess() {')
p.write_text(s)
print('PASS: adjustable smaller vector cursor, spaced larger mouse buttons, persisted zoom hide and refined button states')
