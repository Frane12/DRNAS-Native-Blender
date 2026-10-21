  private final java.util.Map<View, DrnasInputHold> drnasInputHolds = new java.util.LinkedHashMap<>();
  private final java.util.Map<View, Runnable> drnasInputResets = new java.util.LinkedHashMap<>();

  private void drnasReleaseAllInputs() {
    for (Runnable reset : drnasInputResets.values()) reset.run();
    for (java.util.Map.Entry<View, DrnasInputHold> entry : drnasInputHolds.entrySet()) {
      entry.getValue().cancel();
      entry.getKey().setPressed(false); entry.getKey().setActivated(false);
      if (entry.getKey() instanceof TextView) {
        TextView text = (TextView)entry.getKey();
        text.setText(text.getText().toString().replace(" •", ""));
      }
    }
  }

  private void drnasBindInput(TextView button, int key, int mouseDown, int mouseUp) {
    final String label = button.getText().toString().replace(" •", "");
    final DrnasInputHold hold = new DrnasInputHold(pressed -> {
      if (mouseDown != 0) drnasSendInput(pressed ? mouseDown : mouseUp, 0, 0, pressed ? 1 : 0);
      else {
        int modifier = key == KeyEvent.KEYCODE_SHIFT_LEFT ? KeyEvent.META_SHIFT_ON
            : key == KeyEvent.KEYCODE_CTRL_LEFT ? KeyEvent.META_CTRL_ON
            : key == KeyEvent.KEYCODE_ALT_LEFT ? KeyEvent.META_ALT_ON : 0;
        if (pressed) drnasStickyModifiers |= modifier;
        else drnasStickyModifiers &= ~modifier;
        nativeOnKey(key, pressed ? KeyEvent.ACTION_DOWN : KeyEvent.ACTION_UP, drnasStickyModifiers);
      }
    }, android.view.ViewConfiguration.getDoubleTapTimeout());
    drnasInputHolds.put(button, hold);
    final float[] origin = new float[2];
    final boolean[] moved = new boolean[1];
    final boolean[] touching = new boolean[1], deferred = new boolean[1];
    final long[] downAt = new long[1];
    final boolean immediate = mouseDown != 0 || key == KeyEvent.KEYCODE_SHIFT_LEFT
        || key == KeyEvent.KEYCODE_CTRL_LEFT || key == KeyEvent.KEYCODE_ALT_LEFT;
    drnasInputResets.put(button, () -> { touching[0] = deferred[0] = false; moved[0] = true; });
    final int slop = android.view.ViewConfiguration.get(this).getScaledTouchSlop();
    button.setOnTouchListener((v, event) -> {
      switch (event.getActionMasked()) {
        case MotionEvent.ACTION_DOWN:
          origin[0] = event.getX(); origin[1] = event.getY(); moved[0] = false;
          touching[0] = true; downAt[0] = event.getEventTime();
          if (mouseDown != 0) v.getParent().requestDisallowInterceptTouchEvent(true);
          // Command keys still activate on UP: swiping the horizontal strip
          // must not accidentally start Move/Rotate/Delete while scrolling.
          deferred[0] = !immediate && !hold.isLatched();
          if (!deferred[0]) hold.down(event.getEventTime());
          break;
        case MotionEvent.ACTION_MOVE:
          if (Math.abs(event.getX() - origin[0]) > slop || Math.abs(event.getY() - origin[1]) > slop) moved[0] = true;
          break;
        case MotionEvent.ACTION_UP:
          touching[0] = false;
          if (deferred[0] && !moved[0]) hold.down(downAt[0]);
          if (deferred[0] && moved[0]) hold.cancel();
          else hold.up(event.getEventTime(), !moved[0]);
          deferred[0] = false;
          if (mouseDown != 0) v.getParent().requestDisallowInterceptTouchEvent(false);
          break;
        case MotionEvent.ACTION_CANCEL:
          touching[0] = deferred[0] = false;
          hold.cancel();
          if (mouseDown != 0) v.getParent().requestDisallowInterceptTouchEvent(false);
          break;
        default: return true;
      }
      button.setPressed(touching[0] && !hold.isLatched());
      button.setActivated(hold.isHeld());
      boolean changed = !button.getText().toString().equals(label + (hold.isLatched() ? " •" : ""));
      button.setText(label + (hold.isLatched() ? " •" : ""));
      button.setContentDescription(label + (hold.isLatched() ? " — zaključano; dodirni za otključavanje" : " — dvostruki dodir za zaključavanje"));
      if (changed && mouseDown == 0) drnasButtonSizes(drnasButtonPercent, false);
      return true;
    });
    button.setOnClickListener(v -> {
      if (hold.isLatched()) hold.cancel();
      else { hold.down(android.os.SystemClock.uptimeMillis()); hold.up(android.os.SystemClock.uptimeMillis(), false); }
      button.setText(label); button.setPressed(false); button.setActivated(false);
    });
  }

  private int drnasMouseButtonPercent = 100;
  private View drnasMouseDock, drnasDockGrip, drnasDockZoomToggle, drnasDockZoomSlider;
  private void drnasMouseButtonSizes(int percent, boolean save) {
    drnasMouseButtonPercent = Math.max(60, Math.min(150, percent));
    float factor = drnasMouseButtonPercent / 100f;
    for (TextView button : drnasResizeTargets.values()) {
      LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dpDrnas(68 * factor), dpDrnas(54 * factor));
      lp.setMargins(dpDrnas(5 * factor), dpDrnas(4), dpDrnas(5 * factor), dpDrnas(4));
      button.setLayoutParams(lp); button.setTextSize(14f * factor);
    }
    if (drnasDockGrip != null) {
      drnasDockGrip.setLayoutParams(new LinearLayout.LayoutParams(dpDrnas(30 * factor), dpDrnas(48 * factor)));
      ((TextView)drnasDockGrip).setTextSize(16 * factor);
    }
    if (drnasDockZoomToggle != null) {
      LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dpDrnas(74 * factor), dpDrnas(48 * factor));
      lp.setMargins(dpDrnas(4 * factor), 0, dpDrnas(4 * factor), 0);
      drnasDockZoomToggle.setLayoutParams(lp); ((TextView)drnasDockZoomToggle).setTextSize(11f * factor);
    }
    if (drnasDockZoomSlider != null) {
      int available = getResources().getDisplayMetrics().widthPixels - dpDrnas(24 + 268 * factor);
      int width = Math.max(dpDrnas(48), Math.min(dpDrnas(120 * factor), available));
      drnasDockZoomSlider.setLayoutParams(new LinearLayout.LayoutParams(width, dpDrnas(48 * factor)));
    }
    if (save) drnasPrefs.edit().putInt("mouse_button_percent", drnasMouseButtonPercent).apply();
    drnasRefreshPanels();
  }

  private void drnasInstallMouseSizeOptions(LinearLayout options) {
    options.addView(drnasUiLabel("VELIČINA MIŠA I ZOOMA"));
    final TextView value = drnasUiLabel(drnasMouseButtonPercent + "% • LMB/RMB i zoom blok");
    options.addView(value);
    SeekBar size = new SeekBar(this); size.setMax(90); size.setProgress(drnasMouseButtonPercent - 60);
    options.addView(size, new LinearLayout.LayoutParams(-1, dpDrnas(42)));
    size.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar b, int progress, boolean user) {
        drnasMouseButtonSizes(progress + 60, user);
        value.setText(drnasMouseButtonPercent + "% • LMB/RMB i zoom blok");
      }
      public void onStartTrackingTouch(SeekBar b) {}
      public void onStopTrackingTouch(SeekBar b) {}
    });
    options.addView(drnasUiLabel("Dvostruki dodir: zaključaj tipku • jedan dodir: otključaj"));
  }
