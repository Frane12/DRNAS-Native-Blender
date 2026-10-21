  /* NativeActivity takes the main Window surface for Vulkan. ViewRootImpl then
   * skips View drawing there. Each control panel needs its own app subwindow.
   * Never create a screen-sized touch window over the native input queue. */
  private final java.util.Map<View, DrnasPanel> drnasPanels =
      new java.util.LinkedHashMap<>();
  private boolean drnasWindowsActive = false;

  private final class DrnasPanel {
    final View view;
    final FrameLayout host;
    final FrameLayout.LayoutParams anchor;
    final android.widget.PopupWindow popup;
    float offsetX, offsetY;
    boolean pending;
    int lastX = Integer.MIN_VALUE, lastY, lastWidth, lastHeight;

    DrnasPanel(View content, FrameLayout.LayoutParams position) {
      view = content;
      anchor = position;
      host = new FrameLayout(BlenderActivity.this);
      host.setSystemUiVisibility(getWindow().getDecorView().getSystemUiVisibility());
      host.addView(view, new FrameLayout.LayoutParams(position.width, position.height));
      popup = new android.widget.PopupWindow(host, 1, 1, false);
      popup.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
      popup.setTouchable(true);
      popup.setOutsideTouchable(false);
      popup.setTouchModal(false);
      popup.setSplitTouchEnabled(true);
      popup.setInputMethodMode(android.widget.PopupWindow.INPUT_METHOD_NOT_NEEDED);
      popup.setAnimationStyle(0);
      view.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, oright, ob) -> {
        if (r - l != oright - ol || b - t != ob - ot) schedule();
      });
    }

    void schedule() {
      if (pending) return;
      pending = true;
      getWindow().getDecorView().postOnAnimation(() -> {
        pending = false;
        update();
      });
    }

    void update() {
      View decor = getWindow().getDecorView();
      if (!drnasWindowsActive || isFinishing() || isDestroyed()
          || decor.getWindowToken() == null || view.getVisibility() != View.VISIBLE) {
        popup.dismiss();
        return;
      }
      int availableWidth = decor.getWidth(), availableHeight = decor.getHeight();
      if (availableWidth <= 0 || availableHeight <= 0) return;
      host.measure(View.MeasureSpec.makeMeasureSpec(availableWidth, View.MeasureSpec.AT_MOST),
                   View.MeasureSpec.makeMeasureSpec(availableHeight, View.MeasureSpec.AT_MOST));
      int width = Math.max(1, Math.min(availableWidth, host.getMeasuredWidth()));
      int height = Math.max(1, Math.min(availableHeight, host.getMeasuredHeight()));
      int horizontal = anchor.gravity & Gravity.HORIZONTAL_GRAVITY_MASK;
      int vertical = anchor.gravity & Gravity.VERTICAL_GRAVITY_MASK;
      int baseX = horizontal == Gravity.RIGHT ? availableWidth - width - anchor.rightMargin
          : horizontal == Gravity.CENTER_HORIZONTAL ? (availableWidth - width) / 2 : anchor.leftMargin;
      int baseY = vertical == Gravity.BOTTOM ? availableHeight - height - anchor.bottomMargin
          : vertical == Gravity.CENTER_VERTICAL ? (availableHeight - height) / 2 : anchor.topMargin;
      int x = Math.max(0, Math.min(availableWidth - width, baseX + Math.round(offsetX)));
      int y = Math.max(0, Math.min(availableHeight - height, baseY + Math.round(offsetY)));
      // Clamp stale saved positions after rotation/resizing so panels stay reachable.
      offsetX = x - baseX;
      offsetY = y - baseY;
      if (!popup.isShowing()) {
        popup.setWidth(width);
        popup.setHeight(height);
        popup.showAtLocation(decor, Gravity.TOP | Gravity.LEFT, x, y);
      } else if (x != lastX || y != lastY || width != lastWidth || height != lastHeight) {
        popup.update(x, y, width, height);
      }
      lastX = x; lastY = y; lastWidth = width; lastHeight = height;
    }
  }

  private void drnasAddPanel(View view, FrameLayout.LayoutParams position) {
    DrnasPanel panel = new DrnasPanel(view, position);
    drnasPanels.put(view, panel);
    panel.schedule();
  }

  private float drnasOffsetX(View view) { return drnasPanels.get(view).offsetX; }
  private float drnasOffsetY(View view) { return drnasPanels.get(view).offsetY; }
  private void drnasSetOffsetX(View view, float value) {
    DrnasPanel panel = drnasPanels.get(view);
    panel.offsetX = value;
    panel.schedule();
  }
  private void drnasSetOffsetY(View view, float value) {
    DrnasPanel panel = drnasPanels.get(view);
    panel.offsetY = value;
    panel.schedule();
  }
  private void drnasPanelVisibility(View view, int visibility) {
    view.setVisibility(visibility);
    DrnasPanel panel = drnasPanels.get(view);
    if (panel != null) {
      if (visibility != View.VISIBLE) panel.popup.dismiss();
      else panel.schedule();
    }
  }
  private void drnasRefreshPanels() {
    for (DrnasPanel panel : drnasPanels.values()) panel.schedule();
  }
  private void drnasHidePanels() {
    for (DrnasPanel panel : drnasPanels.values()) panel.popup.dismiss();
  }

  @Override protected void onResume() {
    super.onResume();
    drnasWindowsActive = true;
    drnasRefreshPanels();
  }

  @Override public void onConfigurationChanged(android.content.res.Configuration config) {
    super.onConfigurationChanged(config);
    getWindow().getDecorView().post(() -> drnasRefreshPanels());
  }
