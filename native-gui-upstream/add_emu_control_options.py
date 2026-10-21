#!/usr/bin/env python3
"""Java-only named command rows and optional relative pointer using existing JNI."""
from pathlib import Path
import sys

file = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java'
s = file.read_text()
assert 'class DrnasPanel' in s and 'installDrnasMouseOptions' not in s

def once(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new, 1)

start = s.index('    drnasSmallKey("TAB",')
end = s.index('    scroll.addView(row,', start)
keys = '''    final LinearLayout top = new LinearLayout(this);
    final LinearLayout bottom = new LinearLayout(this);
    row.setOrientation(LinearLayout.VERTICAL);
    top.setGravity(Gravity.CENTER_VERTICAL);
    bottom.setGravity(Gravity.CENTER_VERTICAL);
    row.addView(top); row.addView(bottom);
'''
for label, key in [('Edit Mode','TAB'),('Move','G'),('Rotate','R'),('Scale','S'),
                   ('Axis X','X'),('Axis Y','Y'),('Axis Z','Z'),('Extrude','E'),
                   ('Box Select','B'),('Select All','A'),('Search','F3'),('Play/Pause','SPACE')]:
    keys += f'    drnasSmallKey("{label}", KeyEvent.KEYCODE_{key}, 0, top);\n'
for label, key in [('Cancel','ESCAPE'),('Confirm','ENTER'),('Delete','FORWARD_DEL')]:
    keys += f'    drnasSmallKey("{label}", KeyEvent.KEYCODE_{key}, 0, bottom);\n'
for label, key, mod in [('Undo','Z','CTRL'),('Save','S','CTRL'),('Duplicate','D','SHIFT')]:
    keys += f'    drnasSmallKey("{label}", KeyEvent.KEYCODE_{key}, KeyEvent.META_{mod}_ON, bottom);\n'
for label, key in [('Front','1'),('Side','3'),('Top','7')]:
    keys += f'    drnasSmallKey("{label}", KeyEvent.KEYCODE_NUMPAD_{key}, 0, bottom);\n'
for label, const in [('Shift','SHIFT'),('Ctrl','CTRL'),('Alt','ALT')]:
    keys += f'''    final Button {label.lower()} = drnasSmallKey("{label}", KeyEvent.KEYCODE_{const}_LEFT, 0, bottom);
    {label.lower()}.setOnClickListener(v -> drnasToggleModifier(KeyEvent.META_{const}_ON,
        KeyEvent.KEYCODE_{const}_LEFT, {label.lower()}));
'''
keys += '''    final Button keyboard = drnasSmallKey("Keyboard", 0, 0, bottom);
    keyboard.setOnClickListener(v -> showKeyboard());
'''
s = s[:start] + keys + s[end:]
once('line.addView(scroll, new LinearLayout.LayoutParams(maxWidth, dpDrnas(60)));',
     'line.addView(scroll, new LinearLayout.LayoutParams(maxWidth, ViewGroup.LayoutParams.WRAP_CONTENT));')
once('      int base = txt.length() > 5 ? 68 : txt.length() > 3 ? 55 : 39;',
     '      int base = Math.max(52, Math.round(button.getPaint().measureText(txt) / getResources().getDisplayMetrics().density / Math.max(0.6f, factor)) + 22);')
once('    button.setTextSize(11f);', '''    button.setTextSize(13f);
    button.setSingleLine(true);
    button.setFocusable(false);
    button.setContentDescription(label);''')
once('      button.setTextSize(10.5f * factor);', '      button.setTextSize(13f * factor);')
once('    background.setColor(bg);', '''    background.setColors(new int[] {Color.argb(180, 54, 79, 101), bg});
    background.setOrientation(android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM);''')
once('    button.setBackground(drnasPill(Color.rgb(29, 54, 79)));', '''    button.setBackground(new android.graphics.drawable.RippleDrawable(
        android.content.res.ColorStateList.valueOf(Color.argb(95, 120, 220, 232)),
        drnasPill(Color.argb(155, 35, 50, 71)), null));''')
once('    options.addView(drnasUiLabel("EDIT: pomakni panel prstom, DONE: spremi položaj"));',
     '    installDrnasMouseOptions(options);\n    options.addView(drnasUiLabel("EDIT: pomakni panel prstom, DONE: spremi položaj"));')
# Match the EMU mouse dock: one movable grip + LMB + RMB + zoom block.
once('    group.setOrientation(LinearLayout.VERTICAL);', '    group.setOrientation(LinearLayout.HORIZONTAL);')
once('    heading.setText("ZOOM / MOVE");', '    heading.setText("⠿");')
once('    group.setBackgroundColor(Color.argb(220, 22, 52, 73));',
     '    group.setBackground(drnasPill(Color.argb(155, 16, 24, 37)));')
once('    group.addView(heading, new LinearLayout.LayoutParams(-1, dpDrnas(26)));',
     '    group.addView(heading, new LinearLayout.LayoutParams(dpDrnas(30), dpDrnas(48)));\n    drnasDockMouseButtons(group);')
once('    drnasPosition(group, "zoom", true, 115, 96, 190, 80);', '''    drnasPosition(group, "zoom", true, 12, 18, 340, 80);
    drnasPanels.get(group).anchor.height = ViewGroup.LayoutParams.WRAP_CONTENT;
    drnasPanels.get(group).anchor.width = ViewGroup.LayoutParams.WRAP_CONTENT;
    group.getLayoutParams().height = ViewGroup.LayoutParams.WRAP_CONTENT;
    group.getLayoutParams().width = ViewGroup.LayoutParams.WRAP_CONTENT;''')
once('      lp.width = dpDrnas(90 * factor);', '      lp.width = dpDrnas(56 * factor);')
once('      lp.height = dpDrnas(66 * factor);', '      lp.height = dpDrnas(48 * factor);')
once('      v.setTextSize(19f * factor);', '      v.setTextSize(13f * factor);')
once('    void update() {', '    void update() {\n      if (!drnasPanels.containsKey(view)) return;')
s = s.replace('drnasPanels.get(view)',
    'drnasPanels.get(drnasDockedMouse.containsKey(view) ? drnasDockedMouse.get(view) : view)')
once('putFloat(key + "_x", drnasOffsetX(v))',
     'putFloat((drnasDockedMouse.containsKey(v) ? "zoom" : key) + "_x", drnasOffsetX(v))')
once('putFloat(key + "_y", drnasOffsetY(v))',
     'putFloat((drnasDockedMouse.containsKey(v) ? "zoom" : key) + "_y", drnasOffsetY(v))')
# Options must scroll on landscape phones; adding controls must not hide the
# bottom switches below the screen edge.
for method in ('setOrientation', 'setPadding', 'setBackground', 'addView'):
    s = s.replace('options.' + method + '(', 'optionRows.' + method + '(')
s = s.replace('installDrnasMouseOptions(options);', 'installDrnasMouseOptions(optionRows);')
once('    final LinearLayout options = new LinearLayout(this);', '''    final android.widget.ScrollView options = new android.widget.ScrollView(this);
    final LinearLayout optionRows = new LinearLayout(this);
    options.addView(optionRows);
    options.setFillViewport(false);''')
once('        dpDrnas(285), ViewGroup.LayoutParams.WRAP_CONTENT,',
     '        dpDrnas(285), Math.max(dpDrnas(160), getResources().getDisplayMetrics().heightPixels - dpDrnas(90)),')
# Track virtual holds without changing JNI names or native semantics.
s = s.replace('nativeOnDrnasInput(', 'drnasSendInput(')
once('  private native void drnasSendInput(int action, float x, float y, float value);',
     '  private native void nativeOnDrnasInput(int action, float x, float y, float value);')
once('    drnasWindowsActive = false;\n    drnasHidePanels();\n    super.onPause();',
     '    drnasWindowsActive = false;\n    drnasHidePanels();\n    super.onPause();')
once('  private void drnasRefreshPanels() {', '  private void drnasRefreshPanels() {\n    drnasRefreshMouseLayer();')
once('  private void drnasHidePanels() {', '  private void drnasHidePanels() {\n    drnasHideMouseLayer();')
anchor = '  private void requestAllFilesAccess() {'
once(anchor, Path(__file__).with_name('drnas_mouse_options.java.inc').read_text() + '\n' + anchor)
file.write_text(s)
print('PASS: named command rows + optional relative mouse/cursor, Java-only JNI reuse')
