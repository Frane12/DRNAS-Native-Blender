#!/usr/bin/env python3
"""Add a compact, EmuDRNAS-style native shortcut strip with size wheel and GUI scale.

Run AFTER create_sdl3_gui_preview.py, add_drnas_controls.py and
patch_shortcut_ui_native.py. Does not launch a full build.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
file = root / "build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java"
s = file.read_text()

def swap(old, new):
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"expected 1 occurrence, got {count}: {old[:100]!r}")
    s = s.replace(old, new, 1)

# IMPORTANT: the NativeActivity creates native GHOST during super.onCreate.
# The persisted DPI must be published to environment *before* that call.
swap("    publishHardwareNames();\n", """    publishHardwareNames();
    final android.content.SharedPreferences scalePrefs =
        getSharedPreferences("drnas_native_controls_v1", MODE_PRIVATE);
    final int percent = Math.max(75, Math.min(200,
        scalePrefs.getInt("blender_ui_percent", 100)));
    try {
      Os.setenv("DRNAS_ANDROID_UI_DPI", Integer.toString(
          Math.round(160f * percent / 100f)), true);
    } catch (Exception e) {
      android.util.Log.w("DRNAS", "Could not set Blender UI DPI", e);
    }
""")

# Existing mouse widgets remain in place and keep their native hold behavior.
swap("    drnasPosition(button, key, left, 14, 96, 90, 66);",
     """    drnasPosition(button, key, left, 14, 96, 90, 66);
    drnasResizeTargets.put(key, button);""")
swap("    installDrnasControls();",
     """    installDrnasControls();
    installDrnasShortcutStrip();""")
swap("  private void addDrnasCommand(LinearLayout row, String label, int androidKey) {",
"""  private final java.util.Map<String, TextView> drnasResizeTargets =
      new java.util.LinkedHashMap<>();
  private final java.util.ArrayList<Button> drnasSmallKeys =
      new java.util.ArrayList<>();
  private android.widget.LinearLayout drnasKeyStrip;
  private int drnasButtonPercent = 100;
  private int drnasStickyModifiers = 0;
  private final int drnasTextWhite = Color.rgb(235, 240, 249);

  /* Compact pill: small DRNAS Emu-like virtual keys, not the soft keyboard. */
  private android.graphics.drawable.GradientDrawable drnasPill(int bg) {
    android.graphics.drawable.GradientDrawable background =
        new android.graphics.drawable.GradientDrawable();
    background.setColor(bg);
    background.setCornerRadius(dpDrnas(9));
    background.setStroke(dpDrnas(1), Color.argb(155, 67, 119, 169));
    return background;
  }

  private void drnasTap(int key, int extraMeta) {
    final int necessary = extraMeta & ~drnasStickyModifiers;
    final int[] flags = {KeyEvent.META_CTRL_ON, KeyEvent.META_SHIFT_ON,
                         KeyEvent.META_ALT_ON};
    final int[] modifierKeys = {KeyEvent.KEYCODE_CTRL_LEFT, KeyEvent.KEYCODE_SHIFT_LEFT,
                                KeyEvent.KEYCODE_ALT_LEFT};
    int meta = drnasStickyModifiers;
    for (int i = 0; i < flags.length; i++) {
      if ((necessary & flags[i]) != 0) {
        meta |= flags[i];
        nativeOnKey(modifierKeys[i], KeyEvent.ACTION_DOWN, meta);
      }
    }
    nativeOnKey(key, KeyEvent.ACTION_DOWN, meta);
    nativeOnKey(key, KeyEvent.ACTION_UP, meta);
    for (int i = flags.length - 1; i >= 0; i--) {
      if ((necessary & flags[i]) != 0) {
        meta &= ~flags[i];
        nativeOnKey(modifierKeys[i], KeyEvent.ACTION_UP, meta);
      }
    }
  }

  private void drnasToggleModifier(int flag, int key, Button button) {
    final boolean enabled = (drnasStickyModifiers & flag) == 0;
    if (enabled) drnasStickyModifiers |= flag;
    else drnasStickyModifiers &= ~flag;
    nativeOnKey(key, enabled ? KeyEvent.ACTION_DOWN : KeyEvent.ACTION_UP,
                drnasStickyModifiers);
    button.setBackground(drnasPill(enabled ? Color.rgb(35, 120, 137) :
                                          Color.rgb(29, 54, 79)));
  }

  private Button drnasSmallKey(String label, int key, int combo, LinearLayout row) {
    Button button = new Button(this);
    button.setAllCaps(false);
    button.setText(label);
    button.setTextColor(drnasTextWhite);
    button.setTextSize(11f);
    button.setPadding(dpDrnas(3), 0, dpDrnas(3), 0);
    button.setMinHeight(0);
    button.setMinimumHeight(0);
    button.setMinWidth(0);
    button.setMinimumWidth(0);
    button.setBackground(drnasPill(Color.rgb(29, 54, 79)));
    button.setOnClickListener(v -> drnasTap(key, combo));
    row.addView(button);
    drnasSmallKeys.add(button);
    return button;
  }

  private void drnasButtonSizes(int progress, boolean save) {
    drnasButtonPercent = Math.max(60, Math.min(150, progress));
    float factor = drnasButtonPercent / 100f;
    for (Button button : drnasSmallKeys) {
      String txt = button.getText().toString();
      int base = txt.length() > 5 ? 68 : txt.length() > 3 ? 55 : 39;
      LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
          dpDrnas(base * factor), dpDrnas(37 * factor));
      lp.setMargins(dpDrnas(2), dpDrnas(2), dpDrnas(2), dpDrnas(2));
      button.setLayoutParams(lp);
      button.setTextSize(10.5f * factor);
    }
    for (java.util.Map.Entry<String, TextView> pair : drnasResizeTargets.entrySet()) {
      TextView v = pair.getValue();
      android.view.ViewGroup.LayoutParams lp = v.getLayoutParams();
      lp.width = dpDrnas(90 * factor);
      lp.height = dpDrnas(66 * factor);
      v.setLayoutParams(lp);
      v.setTextSize(19f * factor);
    }
    if (save && drnasPrefs != null) {
      drnasPrefs.edit().putInt("button_percent", drnasButtonPercent).apply();
    }
  }

  private TextView drnasUiLabel(String text) {
    TextView label = new TextView(this);
    label.setText(text);
    label.setTextColor(drnasTextWhite);
    label.setGravity(Gravity.CENTER);
    label.setTextSize(12f);
    return label;
  }

  private void installDrnasShortcutStrip() {
    drnasButtonPercent = Math.max(60, Math.min(150,
        drnasPrefs.getInt("button_percent", 100)));

    final LinearLayout line = new LinearLayout(this);
    line.setOrientation(LinearLayout.HORIZONTAL);
    line.setGravity(Gravity.CENTER_VERTICAL);
    line.setPadding(dpDrnas(3), dpDrnas(2), dpDrnas(3), dpDrnas(2));
    line.setBackground(drnasPill(Color.argb(238, 17, 34, 53)));

    final Button opener = new Button(this);
    opener.setText("⌨");
    opener.setAllCaps(false);
    opener.setTextColor(drnasTextWhite);
    opener.setTextSize(17);
    opener.setPadding(0, 0, 0, 0);
    opener.setMinWidth(0); opener.setMinimumWidth(0);
    opener.setMinHeight(0); opener.setMinimumHeight(0);
    opener.setBackground(drnasPill(Color.rgb(37, 82, 114)));
    line.addView(opener, new LinearLayout.LayoutParams(dpDrnas(47), dpDrnas(42)));

    final android.widget.HorizontalScrollView scroll =
        new android.widget.HorizontalScrollView(this);
    scroll.setHorizontalScrollBarEnabled(false);
    scroll.setFillViewport(false);
    scroll.setVisibility(View.GONE);
    final LinearLayout row = new LinearLayout(this);
    row.setOrientation(LinearLayout.HORIZONTAL);
    row.setGravity(Gravity.CENTER_VERTICAL);

    drnasSmallKey("TAB", KeyEvent.KEYCODE_TAB, 0, row);
    drnasSmallKey("G", KeyEvent.KEYCODE_G, 0, row);
    drnasSmallKey("R", KeyEvent.KEYCODE_R, 0, row);
    drnasSmallKey("S", KeyEvent.KEYCODE_S, 0, row);
    drnasSmallKey("X", KeyEvent.KEYCODE_X, 0, row);
    drnasSmallKey("Y", KeyEvent.KEYCODE_Y, 0, row);
    drnasSmallKey("Z", KeyEvent.KEYCODE_Z, 0, row);
    drnasSmallKey("A", KeyEvent.KEYCODE_A, 0, row);
    drnasSmallKey("E", KeyEvent.KEYCODE_E, 0, row);
    drnasSmallKey("I", KeyEvent.KEYCODE_I, 0, row);
    drnasSmallKey("F3", KeyEvent.KEYCODE_F3, 0, row);
    drnasSmallKey("ESC", KeyEvent.KEYCODE_ESCAPE, 0, row);
    drnasSmallKey("DEL", KeyEvent.KEYCODE_FORWARD_DEL, 0, row);
    drnasSmallKey("1", KeyEvent.KEYCODE_NUMPAD_1, 0, row);
    drnasSmallKey("3", KeyEvent.KEYCODE_NUMPAD_3, 0, row);
    drnasSmallKey("7", KeyEvent.KEYCODE_NUMPAD_7, 0, row);
    drnasSmallKey("F12", KeyEvent.KEYCODE_F12, 0, row);
    drnasSmallKey("UNDO", KeyEvent.KEYCODE_Z, KeyEvent.META_CTRL_ON, row);
    drnasSmallKey("DUP", KeyEvent.KEYCODE_D, KeyEvent.META_SHIFT_ON, row);
    final Button shift = drnasSmallKey("SHIFT", KeyEvent.KEYCODE_SHIFT_LEFT, 0, row);
    shift.setOnClickListener(v -> drnasToggleModifier(KeyEvent.META_SHIFT_ON,
                                                  KeyEvent.KEYCODE_SHIFT_LEFT, shift));
    final Button ctrl = drnasSmallKey("CTRL", KeyEvent.KEYCODE_CTRL_LEFT, 0, row);
    ctrl.setOnClickListener(v -> drnasToggleModifier(KeyEvent.META_CTRL_ON,
                                                KeyEvent.KEYCODE_CTRL_LEFT, ctrl));
    scroll.addView(row, new android.widget.HorizontalScrollView.LayoutParams(
        ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
    final int maxWidth = Math.max(dpDrnas(150),
        Math.min(dpDrnas(610),
            getResources().getDisplayMetrics().widthPixels - dpDrnas(360)));
    line.addView(scroll, new LinearLayout.LayoutParams(maxWidth, dpDrnas(60)));
    opener.setOnClickListener(v -> {
      boolean expand = scroll.getVisibility() != View.VISIBLE;
      scroll.setVisibility(expand ? View.VISIBLE : View.GONE);
      opener.setText(expand ? "✕" : "⌨");
    });

    final Button settings = new Button(this);
    settings.setText("⚙");
    settings.setAllCaps(false);
    settings.setTextColor(drnasTextWhite);
    settings.setTextSize(16f);
    settings.setPadding(0, 0, 0, 0);
    settings.setMinWidth(0); settings.setMinimumWidth(0);
    settings.setMinHeight(0); settings.setMinimumHeight(0);
    settings.setBackground(drnasPill(Color.rgb(37, 82, 114)));
    line.addView(settings, new LinearLayout.LayoutParams(dpDrnas(44), dpDrnas(42)));

    final FrameLayout.LayoutParams location = new FrameLayout.LayoutParams(
        ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
        Gravity.TOP | Gravity.LEFT);
    location.topMargin = dpDrnas(6);
    location.leftMargin = dpDrnas(7);
    addContentView(line, location);
    line.setTranslationX(drnasPrefs.getFloat("shortcut_strip_x", 0));
    line.setTranslationY(drnasPrefs.getFloat("shortcut_strip_y", 0));

    final LinearLayout options = new LinearLayout(this);
    options.setOrientation(LinearLayout.VERTICAL);
    options.setPadding(dpDrnas(10), dpDrnas(8), dpDrnas(10), dpDrnas(8));
    options.setBackground(drnasPill(Color.argb(248, 15, 30, 47)));

    final TextView wheelHeading = drnasUiLabel("VELIČINA TIPKI • kotačić / – +");
    options.addView(wheelHeading);
    final LinearLayout wheel = new LinearLayout(this);
    wheel.setGravity(Gravity.CENTER_VERTICAL);
    final Button smaller = new Button(this);
    smaller.setText("−"); smaller.setAllCaps(false);
    final Button larger = new Button(this);
    larger.setText("+"); larger.setAllCaps(false);
    final android.widget.SeekBar sizeSeek = new android.widget.SeekBar(this);
    sizeSeek.setMax(90);  // 60% to 150%.
    sizeSeek.setProgress(drnasButtonPercent - 60);
    wheel.addView(smaller, new LinearLayout.LayoutParams(dpDrnas(50), dpDrnas(44)));
    wheel.addView(sizeSeek, new LinearLayout.LayoutParams(dpDrnas(155), dpDrnas(44)));
    wheel.addView(larger, new LinearLayout.LayoutParams(dpDrnas(50), dpDrnas(44)));
    options.addView(wheel);
    final TextView sizeValue = drnasUiLabel(drnasButtonPercent + "% • LMB/RMB + shortcut tipke");
    options.addView(sizeValue);
    sizeSeek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(android.widget.SeekBar b, int p, boolean fromUser) {
        drnasButtonSizes(p + 60, true);
        sizeValue.setText(drnasButtonPercent + "% • LMB/RMB + shortcut tipke");
      }
      public void onStartTrackingTouch(android.widget.SeekBar b) {}
      public void onStopTrackingTouch(android.widget.SeekBar b) {}
    });
    smaller.setOnClickListener(v -> sizeSeek.setProgress(Math.max(0, sizeSeek.getProgress() - 5)));
    larger.setOnClickListener(v -> sizeSeek.setProgress(Math.min(90, sizeSeek.getProgress() + 5)));

    /* Android ACTION_SCROLL supports actual Bluetooth mouse wheels and
       stylus scroll. Normal scroll over Blender remains untouched. */
    android.view.View.OnGenericMotionListener resizeOnWheel = (v, event) -> {
      if (event.getActionMasked() != android.view.MotionEvent.ACTION_SCROLL) return false;
      float delta = event.getAxisValue(android.view.MotionEvent.AXIS_VSCROLL);
      if (delta == 0) return false;
      sizeSeek.setProgress(Math.max(0, Math.min(90,
          sizeSeek.getProgress() + (delta > 0 ? 5 : -5))));
      return true;
    };
    line.setOnGenericMotionListener(resizeOnWheel);
    opener.setOnGenericMotionListener(resizeOnWheel);
    settings.setOnGenericMotionListener(resizeOnWheel);
    scroll.setOnGenericMotionListener(resizeOnWheel);
    for (Button key : drnasSmallKeys) key.setOnGenericMotionListener(resizeOnWheel);
    options.addView(drnasUiLabel("VELIČINA BLENDER GUI (UI SCALE)"));
    final TextView guiLabel = drnasUiLabel("100%  • promjena nakon ponovnog pokretanja");
    options.addView(guiLabel);
    final android.widget.SeekBar uiSeek = new android.widget.SeekBar(this);
    uiSeek.setMax(125);  // 75..200%.
    final int loaded = Math.max(75, Math.min(200,
        drnasPrefs.getInt("blender_ui_percent", 100)));
    uiSeek.setProgress(loaded - 75);
    options.addView(uiSeek, new LinearLayout.LayoutParams(dpDrnas(260), dpDrnas(45)));
    guiLabel.setText(loaded + "%  • primjena nakon restarta");
    uiSeek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(android.widget.SeekBar b, int p, boolean user) {
        guiLabel.setText((p + 75) + "%  • primjena nakon restarta");
        if (user) drnasPrefs.edit().putInt("blender_ui_percent", p + 75).apply();
      }
      public void onStartTrackingTouch(android.widget.SeekBar b) {}
      public void onStopTrackingTouch(android.widget.SeekBar b) {
        android.widget.Toast.makeText(BlenderActivity.this,
            "Blender GUI veličina sprema se za iduće pokretanje.",
            android.widget.Toast.LENGTH_SHORT).show();
      }
    });
    options.addView(drnasUiLabel("EDIT: pomakni panel prstom, DONE: spremi položaj"));
    drnasEnableDrag(wheelHeading, line, "shortcut_strip");

    final FrameLayout.LayoutParams settingPosition = new FrameLayout.LayoutParams(
        dpDrnas(285), ViewGroup.LayoutParams.WRAP_CONTENT,
        Gravity.TOP | Gravity.LEFT);
    settingPosition.leftMargin = dpDrnas(8);
    settingPosition.topMargin = dpDrnas(63);
    options.setVisibility(View.GONE);
    addContentView(options, settingPosition);
    settings.setOnClickListener(v -> options.setVisibility(
        options.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE));

    drnasButtonSizes(drnasButtonPercent, false);
  }

  private void addDrnasCommand(LinearLayout row, String label, int androidKey) {""")

file.write_text(s)
print("PASS: DRNAS shortcut strip, persistent size wheel and per-device Blender UI scale")
