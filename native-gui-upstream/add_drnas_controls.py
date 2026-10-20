#!/usr/bin/env python3
"""Extend pinned Blender Android activity with real DRNAS GHOST controls.

Run after create_sdl3_gui_preview.py and after patch_native_ghost.py.
Requires freshly rebuilt libblender.so from the patched native source.
"""
from pathlib import Path
import sys
a = Path(sys.argv[1]) / "app/src/main/java/org/blender/blender/BlenderActivity.java"
s = a.read_text()

def once(old, new):
    global s
    assert s.count(old) == 1, f"Expected one occurrence ({s.count(old)}): {old[:120]}"
    s = s.replace(old, new)

once("import android.widget.LinearLayout;", "import android.widget.LinearLayout;\nimport android.widget.SeekBar;\nimport android.widget.TextView;\nimport android.view.MotionEvent;")
once("  private native void nativeOnKey(int keycode, int action, int metaState);",
     """  private native void nativeOnKey(int keycode, int action, int metaState);
  /* Native GHOST JNI implemented in the source-level patched libblender.so. */
  private native void nativeOnDrnasInput(int action, float x, float y, float value);""")
once("    addContentView(bar, params);", """    addContentView(bar, params);
    final Button edit = new Button(this);
    edit.setText("EDIT");
    edit.setAllCaps(false);
    edit.setTextSize(11);
    edit.setMinWidth(0);
    edit.setMinimumWidth(0);
    bar.addView(edit, 0, new LinearLayout.LayoutParams(dpDrnas(64), dpDrnas(45)));
    edit.setOnClickListener(v -> {
      drnasEdit = !drnasEdit;
      edit.setText(drnasEdit ? "DONE" : "EDIT");
    });
    final Button sens = new Button(this);
    sens.setText("SENS");
    sens.setAllCaps(false);
    sens.setTextSize(11);
    sens.setMinWidth(0);
    sens.setMinimumWidth(0);
    bar.addView(sens, 1, new LinearLayout.LayoutParams(dpDrnas(64), dpDrnas(45)));
    sens.setOnClickListener(v -> drnasSensitivity.setVisibility(
        drnasSensitivity.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE)); 
    installDrnasControls();""")
anchor="  private void addDrnasCommand(LinearLayout row, String label, int androidKey) {"
methods="""
  /* The panel is completely separate from the native Blender canvas.
   * Touches outside these widgets still go directly to native Android GHOST. */
  private boolean drnasEdit = false;
  private View drnasSensitivity;
  private int drnasZoomPrevious = 50;
  private android.content.SharedPreferences drnasPrefs;

  private void drnasPosition(View view, String name, boolean left, int insetDp,
                             int bottomDp, int widthDp, int heightDp) {
    FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
        dpDrnas(widthDp), dpDrnas(heightDp),
        Gravity.BOTTOM | (left ? Gravity.LEFT : Gravity.RIGHT));
    if (left) lp.leftMargin = dpDrnas(insetDp);
    else lp.rightMargin = dpDrnas(insetDp);
    lp.bottomMargin = dpDrnas(bottomDp);
    addContentView(view, lp);
    view.setTranslationX(drnasPrefs.getFloat(name + "_x", 0f));
    view.setTranslationY(drnasPrefs.getFloat(name + "_y", 0f));
  }

  private void drnasEnableDrag(View handle, View target, String name) {
    final float[] last = new float[2];
    handle.setOnTouchListener((v, e) -> {
      if (!drnasEdit) return false;
      switch (e.getActionMasked()) {
        case MotionEvent.ACTION_DOWN:
          last[0] = e.getRawX(); last[1] = e.getRawY();
          return true;
        case MotionEvent.ACTION_MOVE:
          target.setTranslationX(target.getTranslationX() + e.getRawX() - last[0]);
          target.setTranslationY(target.getTranslationY() + e.getRawY() - last[1]);
          last[0] = e.getRawX(); last[1] = e.getRawY();
          return true;
        case MotionEvent.ACTION_UP:
          drnasPrefs.edit().putFloat(name + "_x", target.getTranslationX())
              .putFloat(name + "_y", target.getTranslationY()).apply();
          return true;
        default:
          return true;
      }
    });
  }

  private void drnasMouse(String label, int down, int up, boolean left, String key) {
    final TextView button = new TextView(this);
    button.setText(label);
    button.setTextSize(19);
    button.setTextColor(Color.WHITE);
    button.setGravity(Gravity.CENTER);
    button.setBackgroundColor(Color.argb(218, 24, 58, 86));
    drnasPosition(button, key, left, 14, 96, 90, 66);
    final float[] last = new float[2];
    button.setOnTouchListener((v, event) -> {
      int action = event.getActionMasked();
      if (drnasEdit) {
        if (action == MotionEvent.ACTION_DOWN) {
          last[0] = event.getRawX(); last[1] = event.getRawY();
          return true;
        }
        if (action == MotionEvent.ACTION_MOVE) {
          v.setTranslationX(v.getTranslationX() + event.getRawX() - last[0]);
          v.setTranslationY(v.getTranslationY() + event.getRawY() - last[1]);
          last[0] = event.getRawX(); last[1] = event.getRawY();
          return true;
        }
        if (action == MotionEvent.ACTION_UP) {
          drnasPrefs.edit().putFloat(key + "_x", v.getTranslationX())
              .putFloat(key + "_y", v.getTranslationY()).apply();
          return true;
        }
        return true;
      }
      if (action == MotionEvent.ACTION_DOWN) {
        nativeOnDrnasInput(down, 0f, 0f, 1f);
        v.setAlpha(0.58f);
        return true;
      }
      if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
        nativeOnDrnasInput(up, 0f, 0f, 0f);
        v.setAlpha(1f);
        return true;
      }
      return true;
    });
  }

  private void installDrnasControls() {
    drnasPrefs = getSharedPreferences("drnas_native_controls_v1", MODE_PRIVATE);
    drnasMouse("LMB", 2, 3, true, "lmb");
    drnasMouse("RMB", 4, 5, false, "rmb");

    final LinearLayout group = new LinearLayout(this);
    group.setOrientation(LinearLayout.VERTICAL);
    group.setGravity(Gravity.CENTER);
    group.setBackgroundColor(Color.argb(220, 22, 52, 73));
    final TextView heading = new TextView(this);
    heading.setText("ZOOM / MOVE");
    heading.setTextSize(12);
    heading.setGravity(Gravity.CENTER);
    heading.setTextColor(Color.WHITE);
    group.addView(heading, new LinearLayout.LayoutParams(-1, dpDrnas(26)));
    SeekBar zoom = new SeekBar(this);
    zoom.setMax(100);
    zoom.setProgress(50);
    group.addView(zoom, new LinearLayout.LayoutParams(dpDrnas(170), dpDrnas(43)));
    drnasPosition(group, "zoom", true, 115, 96, 190, 80);
    drnasEnableDrag(heading, group, "zoom");
    zoom.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar bar, int progress, boolean byUser) {
        if (!byUser || drnasEdit) return;
        int difference = progress - drnasZoomPrevious;
        drnasZoomPrevious = progress;
        if (difference != 0) nativeOnDrnasInput(6, 0f, 0f, difference / 5.0f);
      }
      public void onStartTrackingTouch(SeekBar bar) {}
      public void onStopTrackingTouch(SeekBar bar) {
        bar.setProgress(50);
        drnasZoomPrevious = 50;
      }
    });
    zoom.setOnTouchListener((v, event) -> {
      if (!drnasEdit) return false;
      return heading.dispatchTouchEvent(event); // EDIT uses heading as a drag handle.
    });

    final LinearLayout speed = new LinearLayout(this);
    speed.setOrientation(LinearLayout.VERTICAL);
    speed.setBackgroundColor(Color.argb(229, 24, 45, 65));
    final TextView speedLabel = new TextView(this);
    speedLabel.setTextColor(Color.WHITE);
    speedLabel.setTextSize(12);
    speedLabel.setGravity(Gravity.CENTER);
    speed.addView(speedLabel, new LinearLayout.LayoutParams(-1, dpDrnas(28)));
    final SeekBar slider = new SeekBar(this);
    slider.setMax(100);
    speed.addView(slider, new LinearLayout.LayoutParams(dpDrnas(210), dpDrnas(40)));
    speed.setVisibility(View.GONE);
    FrameLayout.LayoutParams speedPosition = new FrameLayout.LayoutParams(
        dpDrnas(240), dpDrnas(72), Gravity.TOP | Gravity.RIGHT);
    speedPosition.topMargin = dpDrnas(62);
    speedPosition.rightMargin = dpDrnas(10);
    addContentView(speed, speedPosition);
    drnasSensitivity = speed;
    final int init = drnasPrefs.getInt("gesture_speed", 11);
    slider.setProgress(init);
    slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar bar, int progress, boolean user) {
        float factor = 0.08f + 0.0092f * progress;
        speedLabel.setText("2 prsta: " + Math.round(factor * 100f) + "% brzine");
        nativeOnDrnasInput(7, 0f, 0f, factor);
        if (user) drnasPrefs.edit().putInt("gesture_speed", progress).apply();
      }
      public void onStartTrackingTouch(SeekBar bar) {}
      public void onStopTrackingTouch(SeekBar bar) {}
    });
    nativeOnDrnasInput(7, 0f, 0f, 0.08f + 0.0092f * init);
  }

  @Override protected void onPause() {
    // Explicit release to avoid stuck virtual buttons when Android backgrounds Blender.
    nativeOnDrnasInput(3, 0f, 0f, 0f);
    nativeOnDrnasInput(5, 0f, 0f, 0f);
    super.onPause();
  }

"""
once(anchor,methods+anchor)
a.write_text(s)
g = (Path(sys.argv[1]) / "app/build.gradle")
text=g.read_text()
assert "applicationId 'hr.drnas.nativeblendergui'" in text
text=text.replace("applicationId 'hr.drnas.nativeblendergui'",
                  "applicationId 'hr.drnas.nativeblendercontrols'")
text=text.replace("versionName '0.1-gui-upstream-lab'",
                  "versionName '0.2-native-drnas-touch'")
g.write_text(text)
print("PASS: GUI control overlay, reposition, sensitivity + JNI integrated")
