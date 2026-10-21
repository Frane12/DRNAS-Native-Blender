#!/usr/bin/env python3
"""Independent mouse/key sizing, tactile depth and double-tap input latches."""
from pathlib import Path
import sys

java = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender'
p = java / 'BlenderActivity.java'
s = p.read_text()

def once(old, new):
    global s
    assert s.count(old) == 1, (old[:110], s.count(old))
    s = s.replace(old, new, 1)

# Keep the existing keyboard setting, but remove its effect on the mouse dock.
a = s.index('    for (java.util.Map.Entry<String, TextView> pair : drnasResizeTargets.entrySet()) {')
b = s.index('    drnasRefreshPanels();', a)
s = s[:a] + s[b:]
s = s.replace('LMB/RMB + shortcut tipke', 'tipkovnica i naredbe')
once('VELIČINA TIPKI • kotačić / – +', 'VELIČINA TIPKOVNICE I NAREDBI')
once('    installDrnasMouseOptions(optionRows);', '    drnasInstallMouseSizeOptions(optionRows);\n    installDrnasMouseOptions(optionRows);')
once('    drnasPosition(group, "zoom", true, 12, 18, 340, 80);', '''    drnasMouseDock = group; drnasDockGrip = heading;
    drnasDockZoomToggle = zoomToggle; drnasDockZoomSlider = zoom;
    group.setClipChildren(false); group.setClipToPadding(false);
    drnasPosition(group, "zoom", true, 12, 18, 340, 80);''')
once('    drnasSendInput(7, 0f, 0f, 0.08f + 0.0092f * init);', '''    drnasSendInput(7, 0f, 0f, 0.08f + 0.0092f * init);
    drnasMouseButtonSizes(drnasPrefs.getInt("mouse_button_percent", drnasPrefs.getInt("button_percent", 100)), false);''')

# Use the same tested state machine for mouse buttons and actual keyboard keys.
a = s.index('    final float[] last = new float[2];', s.index('  private void drnasMouse('))
b = s.index('\n  }\n\n  private void installDrnasControls()', a)
s = s[:a] + '    drnasBindInput(button, 0, down, up);\n' + s[b:]
once('    button.setOnClickListener(v -> drnasTap(key, combo));', '''    if (key != 0 && combo == 0) drnasBindInput(button, key, 0, 0);
    else button.setOnClickListener(v -> drnasTap(key, combo));''')
for name, const in [('shift', 'SHIFT'), ('ctrl', 'CTRL'), ('alt', 'ALT')]:
    once(f'    {name}.setOnClickListener(v -> drnasToggleModifier(KeyEvent.META_{const}_ON,\n        KeyEvent.KEYCODE_{const}_LEFT, {name}));',
         f'    drnasBindInput({name}, KeyEvent.KEYCODE_{const}_LEFT, 0, 0);')
once('  @Override protected void onPause() {', '  @Override protected void onPause() {\n    drnasReleaseAllInputs();')
once('    drnasExitDialogOpen = true;', '    drnasStopSpringZoom();\n    drnasReleaseAllInputs();\n    drnasExitDialogOpen = true;')
once('      drnasRelativeMouse = enabled;', '      drnasReleaseAllInputs();\n      drnasRelativeMouse = enabled;')

# Shadows need breathing room, and animated depth must not change hit rectangles.
once('      host.setMotionEventSplittingEnabled(true);', '''      host.setMotionEventSplittingEnabled(true);
      host.setClipChildren(false); host.setClipToPadding(false);''')
once('    row.setOrientation(LinearLayout.VERTICAL);', '''    row.setOrientation(LinearLayout.VERTICAL);
    row.setClipChildren(false); row.setClipToPadding(false);
    top.setClipChildren(false); top.setClipToPadding(false);
    bottom.setClipChildren(false); bottom.setClipToPadding(false);''')
once('    button.setElevation(dpDrnas(2));', '''    button.setElevation(dpDrnas(5));
    android.animation.StateListAnimator feedback = new android.animation.StateListAnimator();
    android.animation.AnimatorSet press = new android.animation.AnimatorSet();
    press.playTogether(android.animation.ObjectAnimator.ofFloat(button, "scaleX", 0.96f),
        android.animation.ObjectAnimator.ofFloat(button, "scaleY", 0.96f),
        android.animation.ObjectAnimator.ofFloat(button, "translationY", dpDrnas(1)),
        android.animation.ObjectAnimator.ofFloat(button, "elevation", dpDrnas(1)));
    press.setDuration(75);
    android.animation.AnimatorSet locked = new android.animation.AnimatorSet();
    locked.playTogether(android.animation.ObjectAnimator.ofFloat(button, "scaleX", 0.985f),
        android.animation.ObjectAnimator.ofFloat(button, "scaleY", 0.985f),
        android.animation.ObjectAnimator.ofFloat(button, "translationY", 0),
        android.animation.ObjectAnimator.ofFloat(button, "elevation", dpDrnas(3)));
    locked.setDuration(90);
    android.animation.AnimatorSet release = new android.animation.AnimatorSet();
    release.playTogether(android.animation.ObjectAnimator.ofFloat(button, "scaleX", 1),
        android.animation.ObjectAnimator.ofFloat(button, "scaleY", 1),
        android.animation.ObjectAnimator.ofFloat(button, "translationY", 0),
        android.animation.ObjectAnimator.ofFloat(button, "elevation", dpDrnas(5)));
    release.setDuration(130);
    feedback.addState(new int[] {android.R.attr.state_pressed}, press);
    feedback.addState(new int[] {android.R.attr.state_activated}, locked);
    feedback.addState(new int[] {}, release);
    button.setStateListAnimator(feedback);''')
once('  private void requestAllFilesAccess() {', Path(__file__).with_name('drnas_hold_bindings.java.inc').read_text() + '\n  private void requestAllFilesAccess() {')
p.write_text(s)
(java / 'DrnasInputHold.java').write_text(Path(__file__).with_name('DrnasInputHold.java').read_text())
print('PASS: independent persisted sizes, tactile button depth, tested double-tap input locks and lifecycle release')
