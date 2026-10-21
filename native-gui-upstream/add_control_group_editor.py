#!/usr/bin/env python3
"""Java/Python-only UI v8, applied after accepted GPU v7 source patch chain."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).resolve().parent
java=root/'build_files/android/apk/app/src/main/java/org/blender/blender'
p=java/'BlenderActivity.java';s=p.read_text()
def once(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new,1)
once('    DrnasGpuOptions.apply(this);','    DrnasGpuOptions.apply(this);\n    DrnasInitLog.start(this);')
once('    super.onResume();','    super.onResume();\n    DrnasInitLog.publish();')
once('    drnasStopSpringZoom();\n    drnasWindowsActive = false;', '    drnasStopSpringZoom();\n    if (drnasEditorPopup != null) drnasEditorPopup.dismiss();\n    drnasWindowsActive = false;')
once('  private void showDrnasExitDialog() {','''  private void showDrnasExitDialog() {
    if (drnasEditorPopup != null && drnasEditorPopup.isShowing()) { drnasEditorPopup.dismiss(); return; }''')
# Bind the actual existing groups, not a second toolbar.
once('    final LinearLayout line = new LinearLayout(this);','    final LinearLayout line = new LinearLayout(this);\n    drnasKeyStrip = line;')
once('    scroll.addView(row, new android.widget.HorizontalScrollView.LayoutParams(','''    drnasEditKeyScroll = scroll; drnasEditKeyRows = row;
    scroll.addView(row, new android.widget.HorizontalScrollView.LayoutParams(''')
once('    drnasEnableDrag(stripGrip, line, "shortcut_strip");','''    drnasEnableDrag(stripGrip, line, "shortcut_strip");
    drnasRestoreKeyOrder();
    drnasKeyGeometry();
    drnasApplyOpacity();
    drnasAttachGear(line, false);
    drnasAttachGear(drnasMouseDock, true);''')
once('      if (changed && mouseDown == 0) drnasButtonSizes(drnasButtonPercent, false);','      if (changed && mouseDown == 0) button.requestLayout();')
# Apply dimensions after the old size control; preserve actual key listeners/state machines.
a=s.index('  private void drnasButtonSizes(');b=s.index('  private TextView drnasUiLabel(',a)
block=s[a:b];assert block.count('    drnasRefreshPanels();')==1
block=block.replace('    drnasRefreshPanels();','    drnasKeyGeometry();\n    drnasRefreshPanels();');s=s[:a]+block+s[b:]
once('    optionRows.addView(sizeValue);','    optionRows.addView(sizeValue);\n    drnasOpacitySlider(optionRows, false);')
once('    options.addView(drnasUiLabel("Dvostruki dodir: zaključaj tipku • jedan dodir: otključaj"));','    drnasOpacitySlider(options, true);\n    options.addView(drnasUiLabel("Dvostruki dodir: zaključaj tipku • jedan dodir: otključaj"));')
# Independent X/Y dimensions for the mouse dock.
a=s.index('  private void drnasMouseButtonSizes(');b=s.index('  private void drnasInstallMouseSizeOptions(',a)
block=s[a:b]
block=block.replace('    float factor = drnasMouseButtonPercent / 100f;','''    float factor = drnasMouseButtonPercent / 100f;
    float wf = Math.min(factor * drnasPrefs.getInt("mouse_width", 100) / 100f,
        (getResources().getDisplayMetrics().widthPixels - dpDrnas(24)) / (float)dpDrnas(398));
    float hf = Math.min(factor * drnasPrefs.getInt("mouse_height", 100) / 100f,
        (getResources().getDisplayMetrics().heightPixels - dpDrnas(60)) / (float)dpDrnas(64));''')
for n in (68,30,74,120):block=block.replace(f'{n} * factor',f'{n} * wf')
for n in (54,48):block=block.replace(f'{n} * factor',f'{n} * hf')
block=block.replace('268 * factor','268 * wf').replace('5 * factor','5 * wf').replace('4 * factor','4 * wf')
block=block.replace('14f * factor','14f * Math.min(wf, hf)').replace('16 * factor','16 * Math.min(wf, hf)').replace('11f * factor','11f * Math.min(wf, hf)')
s=s[:a]+block+s[b:]
once('  private void requestAllFilesAccess() {',(here/'drnas_control_editor.java.inc').read_text()+'\n  private void requestAllFilesAccess() {')
p.write_text(s)
(java/'DrnasInitLog.java').write_text((here/'DrnasInitLog.java').read_text())
# Stretch uses Android's full window + existing native aspect-fit buffer scaling.
# No native code/env pretending to force an unsupported fixed-aspect buffer.
p=java/'DrnasGpuOptions.java';s=p.read_text()
def gpu_once(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new,1)
gpu_once('    renderer=DrnasGpuProfile.renderer;','    applyStretch(a);\n    renderer=DrnasGpuProfile.renderer;')
gpu_once('    rows.addView(pending);','''    android.widget.CheckBox stretch=new android.widget.CheckBox(a);
    stretch.setText("Stretch screen • popuni cijeli zaslon"); stretch.setTextColor(Color.WHITE);
    stretch.setChecked(p.getBoolean("stretch_screen",false)); rows.addView(stretch);
    stretch.setOnCheckedChangeListener((v,enabled)->{
      p.edit().putBoolean("stretch_screen",enabled).apply();
      applyStretch(a);
      pending.setText("Stretch spremljen. Manja rezolucija skalira se na cijeli prozor; omjer slike ostaje očuvan.");
    });
    rows.addView(pending);
    TextView log=label(a,"GPU init log: " + DrnasInitLog.path()); rows.addView(log);''')
gpu_once('  private DrnasGpuOptions(){}','''  public static void applyStretch(Activity a) {
    boolean fill=prefs(a).getBoolean("stretch_screen",false);
    android.view.Window window=a.getWindow();
    android.view.WindowManager.LayoutParams lp=window.getAttributes();
    lp.layoutInDisplayCutoutMode=fill ? android.view.WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS
        : android.view.WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_DEFAULT;
    window.setAttributes(lp);
    window.setDecorFitsSystemWindows(!fill);
    if(fill) {
      window.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE
          | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
          | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
      if (window.getInsetsController()!=null) window.getInsetsController().hide(android.view.WindowInsets.Type.systemBars());
    }
  }
  private DrnasGpuOptions(){}''')
s=s.replace('Aktivno pri pokretanju:','Zatraženo pri pokretanju:')
p.write_text(s)
# Separate install because v7's ephemeral CI signing certificate is unavailable.
p=root/'build_files/android/apk/app/src/main/AndroidManifest.xml';s=p.read_text().replace('hr.drnas.blendernativegputest2026v7','hr.drnas.blendernativecontrolstest2026v8').replace('android:versionCode="8"','android:versionCode="9"').replace('0.1.7-gpu-resolution-test','0.1.8-control-editor-test').replace('Native Blender GPU TEST','Native Blender Controls v8 TEST');p.write_text(s)
print('PASS: group gears, live XY geometry/order, opacity, stretch window and bounded GPU init report; native unchanged')
