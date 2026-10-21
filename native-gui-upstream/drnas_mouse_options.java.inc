  private boolean drnasRelativeMouse, drnasPointerEffect = true;
  private float drnasMouseSpeed = 1f, drnasPointerX = -1f, drnasPointerY = -1f;
  private int drnasHeldMouseButtons;
  private long drnasClickEffectUntil;
  private android.widget.PopupWindow drnasMouseWindow, drnasPointerWindow;
  private View drnasMousePad;
  private DrnasPointer drnasPointer;
  private boolean drnasPointerPending;

  private void drnasDockMouseButtons(LinearLayout dock) {
    for (String key : new String[] {"lmb", "rmb"}) {
      TextView button = drnasResizeTargets.get(key);
      DrnasPanel old = drnasPanels.remove(button);
      if (old != null) old.popup.dismiss();
      ((ViewGroup)button.getParent()).removeView(button);
      dock.addView(button, new LinearLayout.LayoutParams(dpDrnas(56), dpDrnas(48)));
      // Mouse widgets now share the dock's saved position. Their EDIT drag
      // handlers still work, while normal DOWN/UP listeners remain unchanged.
      drnasDockedMouse.put(button, dock);
    }
  }
  private final java.util.Map<View, View> drnasDockedMouse = new java.util.HashMap<>();

  private void drnasSendInput(int action, float x, float y, float value) {
    if (action == 2 || action == 4) {
      drnasClickEffectUntil = android.os.SystemClock.uptimeMillis() + 180;
      if (drnasPointer != null) drnasPointer.postInvalidateDelayed(190);
    }
    if (action == 2) drnasHeldMouseButtons |= 1;
    if (action == 3) drnasHeldMouseButtons &= ~1;
    if (action == 4) drnasHeldMouseButtons |= 2;
    if (action == 5) drnasHeldMouseButtons &= ~2;
    nativeOnDrnasInput(action, x, y, value);
    if (action >= 2 && action <= 5) drnasUpdatePointer();
  }

  private void installDrnasMouseOptions(LinearLayout options) {
    drnasRelativeMouse = drnasPrefs.getBoolean("relative_mouse", false);
    drnasPointerEffect = drnasPrefs.getBoolean("pointer_effect", true);
    drnasMouseSpeed = drnasPrefs.getInt("mouse_speed", 100) / 100f;
    android.widget.Switch mode = new android.widget.Switch(this);
    mode.setText("Miš / touchpad (isključeno: direktni dodir)");
    mode.setTextColor(drnasTextWhite);
    mode.setTextSize(12);
    mode.setChecked(drnasRelativeMouse);
    options.addView(mode);
    mode.setOnCheckedChangeListener((v, enabled) -> {
      drnasSendInput(3, 0, 0, 0); drnasSendInput(5, 0, 0, 0);
      drnasRelativeMouse = enabled;
      drnasPointerX = drnasPointerY = -1;
      drnasPrefs.edit().putBoolean("relative_mouse", enabled).apply();
      drnasHidePanels();
      drnasRefreshPanels();
    });
    android.widget.Switch effect = new android.widget.Switch(this);
    effect.setText("Efekt pokazivača / krug klika (miš način)");
    effect.setTextColor(drnasTextWhite);
    effect.setTextSize(12);
    effect.setChecked(drnasPointerEffect);
    options.addView(effect);
    effect.setOnCheckedChangeListener((v, enabled) -> {
      drnasPointerEffect = enabled;
      drnasPrefs.edit().putBoolean("pointer_effect", enabled).apply();
      drnasUpdatePointer();
    });
    TextView speedLabel = drnasUiLabel("Brzina miša: " + Math.round(drnasMouseSpeed * 100) + "%");
    options.addView(speedLabel);
    SeekBar speed = new SeekBar(this);
    speed.setMax(175); speed.setProgress(Math.round(drnasMouseSpeed * 100) - 25);
    options.addView(speed, new LinearLayout.LayoutParams(-1, dpDrnas(36)));
    speed.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar b, int p, boolean user) {
        drnasMouseSpeed = (p + 25) / 100f;
        speedLabel.setText("Brzina miša: " + (p + 25) + "%");
        if (user) drnasPrefs.edit().putInt("mouse_speed", p + 25).apply();
      }
      public void onStartTrackingTouch(SeekBar b) {}
      public void onStopTrackingTouch(SeekBar b) {}
    });
    options.addView(drnasUiLabel("Miš: tap = lijevi klik • 2 prsta = zoom / desni tap"));
  }

  private void drnasRefreshMouseLayer() {
    if (!drnasWindowsActive || !drnasRelativeMouse || isFinishing() || isDestroyed()) {
      drnasHideMouseLayer(); return;
    }
    View decor = getWindow().getDecorView();
    if (decor.getWindowToken() == null || decor.getWidth() <= 0) return;
    if (drnasMouseWindow == null) {
      drnasMousePad = new View(this);
      drnasMousePad.setSystemUiVisibility(decor.getSystemUiVisibility());
      drnasMousePad.setOnTouchListener(new DrnasTrackpad());
      // Hardware mouse buttons/hover still use the same native input bridge.
      drnasMousePad.setOnHoverListener((v, e) -> { drnasMovePointer(e.getX(), e.getY()); return true; });
      drnasMousePad.setOnGenericMotionListener((v, e) -> {
        drnasMovePointer(e.getX(), e.getY());
        if (e.getActionMasked() == MotionEvent.ACTION_SCROLL) {
          drnasSendInput(6, 0, 0, e.getAxisValue(MotionEvent.AXIS_VSCROLL));
          return true;
        }
        if (e.getActionMasked() == MotionEvent.ACTION_BUTTON_PRESS
            || e.getActionMasked() == MotionEvent.ACTION_BUTTON_RELEASE) {
          boolean left = (e.getButtonState() & MotionEvent.BUTTON_PRIMARY) != 0;
          boolean right = (e.getButtonState() & MotionEvent.BUTTON_SECONDARY) != 0;
          if (left != ((drnasHeldMouseButtons & 1) != 0)) drnasSendInput(left ? 2 : 3, 0, 0, 0);
          if (right != ((drnasHeldMouseButtons & 2) != 0)) drnasSendInput(right ? 4 : 5, 0, 0, 0);
          return true;
        }
        return false;
      });
      drnasMouseWindow = new android.widget.PopupWindow(drnasMousePad, -1, -1, false);
      drnasMouseWindow.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
      drnasMouseWindow.setTouchModal(false);
      drnasMouseWindow.setSplitTouchEnabled(true);
      drnasMouseWindow.setInputMethodMode(android.widget.PopupWindow.INPUT_METHOD_NOT_NEEDED);
      drnasMouseWindow.setAnimationStyle(0);
      drnasPointer = new DrnasPointer();
      drnasPointerWindow = new android.widget.PopupWindow(drnasPointer, dpDrnas(38), dpDrnas(38), false);
      drnasPointerWindow.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
      drnasPointerWindow.setTouchable(false);
      drnasPointerWindow.setTouchModal(false);
      drnasPointerWindow.setAnimationStyle(0);
    }
    if (!drnasMouseWindow.isShowing()) drnasMouseWindow.showAtLocation(decor, Gravity.TOP | Gravity.LEFT, 0, 0);
    if (drnasPointerX < 0) drnasMovePointer(decor.getWidth() / 2f, decor.getHeight() / 2f);
    drnasUpdatePointer();
  }

  private void drnasHideMouseLayer() {
    if (drnasMouseWindow != null) drnasMouseWindow.dismiss();
    if (drnasPointerWindow != null) drnasPointerWindow.dismiss();
  }

  private void drnasMovePointer(float x, float y) {
    View decor = getWindow().getDecorView();
    drnasPointerX = Math.max(0, Math.min(decor.getWidth() - 1, x));
    drnasPointerY = Math.max(0, Math.min(decor.getHeight() - 1, y));
    drnasSendInput(1, drnasPointerX, drnasPointerY, 0);
    drnasUpdatePointer();
  }

  private void drnasUpdatePointer() {
    if (drnasPointerPending) return;
    drnasPointerPending = true;
    getWindow().getDecorView().postOnAnimation(() -> {
      drnasPointerPending = false;
      if (drnasPointerWindow == null) return;
      if (!drnasWindowsActive || !drnasRelativeMouse) { drnasPointerWindow.dismiss(); return; }
      int x = Math.round(drnasPointerX) - dpDrnas(4), y = Math.round(drnasPointerY) - dpDrnas(4);
      if (!drnasPointerWindow.isShowing())
        drnasPointerWindow.showAtLocation(getWindow().getDecorView(), Gravity.TOP | Gravity.LEFT, x, y);
      else drnasPointerWindow.update(x, y, -1, -1);
      drnasPointer.invalidate();
    });
  }

  private final class DrnasTrackpad implements View.OnTouchListener {
    float lastX, lastY, travel;
    long started;
    boolean multiple, heldAtStart;
    public boolean onTouch(View v, MotionEvent e) {
      int action = e.getActionMasked();
      if (e.isFromSource(android.view.InputDevice.SOURCE_MOUSE)) {
        drnasMovePointer(e.getX(), e.getY());
        int buttons = e.getButtonState();
        if (action == MotionEvent.ACTION_CANCEL) buttons = 0;
        boolean left = (buttons & MotionEvent.BUTTON_PRIMARY) != 0;
        boolean right = (buttons & MotionEvent.BUTTON_SECONDARY) != 0;
        if (left != ((drnasHeldMouseButtons & 1) != 0)) drnasSendInput(left ? 2 : 3, 0, 0, 0);
        if (right != ((drnasHeldMouseButtons & 2) != 0)) drnasSendInput(right ? 4 : 5, 0, 0, 0);
        return true;
      }
      if (drnasEdit) return true;
      if (action == MotionEvent.ACTION_DOWN) {
        lastX = e.getX(); lastY = e.getY(); travel = 0;
        started = e.getEventTime(); multiple = false;
        heldAtStart = drnasHeldMouseButtons != 0;
      } else if (action == MotionEvent.ACTION_POINTER_DOWN) {
        multiple = true; lastY = (e.getY(0) + e.getY(1)) / 2;
      } else if (action == MotionEvent.ACTION_MOVE) {
        if (e.getPointerCount() > 1) {
          float y = (e.getY(0) + e.getY(1)) / 2;
          float delta = y - lastY;
          travel += Math.abs(delta);
          drnasSendInput(6, 0, 0, -delta / dpDrnas(20)); lastY = y;
        } else {
          float dx = e.getX() - lastX, dy = e.getY() - lastY;
          travel += Math.abs(dx) + Math.abs(dy);
          if (!multiple) drnasMovePointer(drnasPointerX + dx * drnasMouseSpeed,
                                         drnasPointerY + dy * drnasMouseSpeed);
          lastX = e.getX(); lastY = e.getY();
        }
      } else if (action == MotionEvent.ACTION_UP) {
        if (!heldAtStart && drnasHeldMouseButtons == 0 && travel < dpDrnas(10)
            && e.getEventTime() - started < 300) {
          drnasSendInput(multiple ? 4 : 2, 0, 0, 1);
          drnasSendInput(multiple ? 5 : 3, 0, 0, 0);
        }
      }
      return true;
    }
  }

  private final class DrnasPointer extends View {
    final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    DrnasPointer() { super(BlenderActivity.this); }
    @Override protected void onDraw(android.graphics.Canvas canvas) {
      super.onDraw(canvas);
      float d = getResources().getDisplayMetrics().density;
      canvas.save(); canvas.scale(d, d);
      if (drnasPointerEffect && (drnasHeldMouseButtons != 0
          || android.os.SystemClock.uptimeMillis() < drnasClickEffectUntil)) {
        paint.setColor(Color.argb(100, 100, 220, 240));
        canvas.drawCircle(12, 12, 11, paint);
      }
      android.graphics.Path arrow = new android.graphics.Path();
      arrow.moveTo(4, 4); arrow.lineTo(4, 24); arrow.lineTo(10, 18);
      arrow.lineTo(15, 28); arrow.lineTo(19, 26); arrow.lineTo(14, 16);
      arrow.lineTo(23, 16); arrow.close();
      paint.setStyle(android.graphics.Paint.Style.FILL); paint.setColor(Color.WHITE);
      canvas.drawPath(arrow, paint);
      paint.setStyle(android.graphics.Paint.Style.STROKE); paint.setStrokeWidth(1.4f);
      paint.setColor(Color.rgb(12, 25, 38)); canvas.drawPath(arrow, paint);
      paint.setStyle(android.graphics.Paint.Style.FILL);
      canvas.restore();
    }
  }
