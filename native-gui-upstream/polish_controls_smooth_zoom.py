#!/usr/bin/env python3
"""Fix dynamic popup width and connect zoom to a Python view-distance bridge."""
from pathlib import Path
import sys

p = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java'
s = p.read_text()

def once(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new, 1)

# The popup must be remeasured explicitly on expansion. A child layout listener
# cannot discover its desired width while the old small window constrains it.
once('      opener.setText(expand ? "✕" : "⌨");', '''      opener.setText(expand ? "⌄" : "⌨");
      drnasPrefs.edit().putBoolean("shortcut_expanded", expand).apply();
      drnasRefreshPanels();''')
once('    scroll.setVisibility(View.GONE);', '''    scroll.setVisibility(drnasPrefs.getBoolean("shortcut_expanded", true) ? View.VISIBLE : View.GONE);''')
once('    opener.setText("⌨");', '    opener.setText(drnasPrefs.getBoolean("shortcut_expanded", true) ? "⌄" : "⌨");')
once('getResources().getDisplayMetrics().widthPixels - dpDrnas(360)',
     'getResources().getDisplayMetrics().widthPixels - dpDrnas(150)')
once('    drnasButtonSizes(drnasButtonPercent, false);', '''    drnasButtonSizes(drnasButtonPercent, false);
    final TextView stripGrip = drnasUiLabel("⠿");
    stripGrip.setContentDescription("Pomakni traku tipki");
    line.addView(stripGrip, 0, new LinearLayout.LayoutParams(dpDrnas(30), dpDrnas(44)));
    drnasEnableDrag(stripGrip, line, "shortcut_strip");''')
once('      int base = Math.max(52, Math.round(button.getPaint().measureText(txt) / getResources().getDisplayMetrics().density / Math.max(0.6f, factor)) + 22);', '''      button.setTextSize(13f * factor);
      int base = Math.max(52, (int)Math.ceil(button.getPaint().measureText(txt)
          / getResources().getDisplayMetrics().density / factor) + 22);''')
once('    if (save && drnasPrefs != null) {', '    drnasRefreshPanels();\n    if (save && drnasPrefs != null) {')
# Avoid a second legacy toolbar over Blender's top-right Outliner.
once('    drnasAddPanel(bar, params);', '    bar.setVisibility(View.GONE);')
once('    handle.setOnTouchListener((v, e) -> {\n      if (!drnasEdit) return false;',
     '    handle.setOnTouchListener((v, e) -> {\n      // Dedicated grip: dragging does not require EDIT mode.')
once('        Gravity.TOP | Gravity.LEFT);\n    location.topMargin = dpDrnas(6);',
     '        Gravity.BOTTOM | Gravity.LEFT);\n    location.bottomMargin = dpDrnas(86);')
once('getResources().getDisplayMetrics().heightPixels - dpDrnas(90)',
     'getResources().getDisplayMetrics().heightPixels - dpDrnas(190)')
once('    installDrnasMouseOptions(optionRows);', '''    installDrnasMouseOptions(optionRows);
    final android.widget.Switch smoothZoom = new android.widget.Switch(this);
    smoothZoom.setText("Smooth zoom (kao EmuDRNAS)");
    smoothZoom.setTextColor(drnasTextWhite); smoothZoom.setTextSize(12);
    smoothZoom.setChecked(drnasSmoothZoomEnabled);
    optionRows.addView(smoothZoom);
    smoothZoom.setOnCheckedChangeListener((v, enabled) -> {
      drnasSmoothZoomEnabled = enabled;
      drnasPrefs.edit().putBoolean("smooth_zoom", enabled).apply();
    });
    final Button gestureSettings = new Button(this);
    gestureSettings.setText("Osjetljivost gesta");
    optionRows.addView(gestureSettings);
    gestureSettings.setOnClickListener(v -> drnasPanelVisibility(drnasSensitivity,
        drnasSensitivity.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE));''')
once('    DrnasGpuProfile.apply(this);', '    startDrnasSmoothZoom();\n    DrnasGpuProfile.apply(this);')
once('    super.onDestroy();', '''    if (drnasZoomThread != null) drnasZoomThread.quitSafely();
    super.onDestroy();''')
once('    nativeOnDrnasInput(action, x, y, value);', '''    if (action == 6 && drnasSmoothZoomEnabled && drnasSmoothZoomReady) {
      drnasOfferZoom(value);
    } else nativeOnDrnasInput(action, x, y, value);''')
anchor = '  private void requestAllFilesAccess() {'
once(anchor, Path(__file__).with_name('drnas_smooth_zoom.java.inc').read_text() + '\n' + anchor)
p.write_text(s)
print('PASS: explicit popup expansion/resize, one command toolbar, smooth zoom bridge')
