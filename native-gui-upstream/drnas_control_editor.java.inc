  // Per-group editor: gear stays visible independently of group transparency.
  private android.widget.HorizontalScrollView drnasEditKeyScroll;
  private LinearLayout drnasEditKeyRows;
  private final java.util.ArrayList<Button> drnasDefaultKeyOrder = new java.util.ArrayList<>();
  private android.widget.PopupWindow drnasEditorPopup;
  private boolean drnasSizingKeys;

  private void drnasOpacitySlider(LinearLayout rows, boolean mouse) {
    String key = mouse ? "mouse_transparency" : "keyboard_transparency";
    drnasEditorSlider(rows, "Prozirnost " + (mouse ? "miša i zooma" : "tipkovnice"), 0, 85,
        drnasPrefs.getInt(key, 0), "%", value -> {
          drnasPrefs.edit().putInt(key, value).apply();
          drnasApplyOpacity();
        });
  }
  private void drnasApplyOpacity() {
    if (drnasMouseDock != null) drnasMouseDock.setAlpha(1f - drnasPrefs.getInt("mouse_transparency", 0) / 100f);
    if (drnasKeyStrip != null) drnasKeyStrip.setAlpha(1f - drnasPrefs.getInt("keyboard_transparency", 0) / 100f);
  }
  private void drnasEditorSlider(LinearLayout rows, String title, int min, int max,
      int value, String suffix, java.util.function.IntConsumer changed) {
    final TextView label = drnasUiLabel(title + ": " + value + suffix);
    label.setPadding(0, dpDrnas(7), 0, 0); rows.addView(label);
    SeekBar bar = new SeekBar(this); bar.setMax(max - min);
    bar.setProgress(Math.max(0, Math.min(max - min, value - min)));
    rows.addView(bar, new LinearLayout.LayoutParams(-1, dpDrnas(42)));
    bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onStartTrackingTouch(SeekBar b) {}
      public void onStopTrackingTouch(SeekBar b) {}
      public void onProgressChanged(SeekBar b, int p, boolean user) {
        label.setText(title + ": " + (p + min) + suffix);
        if (user) changed.accept(p + min);
      }
    });
  }
  private void drnasKeyGeometry() {
    if (drnasEditKeyRows == null || drnasEditKeyScroll == null || drnasSizingKeys) return;
    // Keep accepted v7 scrolling layout until the user edits geometry/order.
    if (!drnasPrefs.contains("keyboard_width") && !drnasPrefs.contains("keyboard_height")
        && !drnasPrefs.contains("keyboard_rows") && !drnasPrefs.contains("keyboard_order")) return;
    drnasSizingKeys = true;
    try {
      for (Button b : drnasSmallKeys) if (b.getParent() instanceof ViewGroup)
        ((ViewGroup)b.getParent()).removeView(b);
      drnasEditKeyRows.removeAllViews();
      int rows = Math.max(1, Math.min(5, drnasPrefs.getInt("keyboard_rows", 2)));
      int count = drnasSmallKeys.size();
      int screen = getWindow().getDecorView().getWidth();
      if (screen <= 0) screen = getResources().getDisplayMetrics().widthPixels;
      int widthPercent = Math.max(40, Math.min(100, drnasPrefs.getInt("keyboard_width", 90)));
      int width = Math.max(dpDrnas(110), Math.min(screen - dpDrnas(120), screen * widthPercent / 100 - dpDrnas(120)));
      // Height controls the whole key area, then every key follows its row.
      int heightPercent = Math.max(60, Math.min(220, drnasPrefs.getInt("keyboard_height", 100)));
      int cellHeight = Math.max(dpDrnas(24), dpDrnas(82f * drnasButtonPercent / 100f * heightPercent / 100f) / rows);
      int maxHeight = Math.max(dpDrnas(60), getResources().getDisplayMetrics().heightPixels - dpDrnas(150));
      cellHeight = Math.min(cellHeight, Math.max(dpDrnas(20), maxHeight / rows));
      drnasEditKeyScroll.setLayoutParams(new LinearLayout.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT));
      drnasEditKeyRows.setLayoutParams(new android.widget.HorizontalScrollView.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT));
      for (int rowIndex = 0; rowIndex < rows; rowIndex++) {
        int start = rowIndex * count / rows, end = (rowIndex + 1) * count / rows;
        LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL);
        row.setClipChildren(false); row.setClipToPadding(false);
        drnasEditKeyRows.addView(row, new LinearLayout.LayoutParams(width, cellHeight));
        for (int i = start; i < end; i++) {
          Button b = drnasSmallKeys.get(i);
          String label = b.getText().toString().replace(" •", "");
          float weight = Math.max(4f, label.length() * 0.65f + 2f);
          LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, Math.max(dpDrnas(18), cellHeight - dpDrnas(4)), weight);
          lp.setMargins(dpDrnas(2), dpDrnas(2), dpDrnas(2), dpDrnas(2));
          b.setPadding(dpDrnas(2), 0, dpDrnas(2), 0);
          b.setAutoSizeTextTypeUniformWithConfiguration(8, Math.max(10, Math.round(14 * drnasButtonPercent / 100f)), 1, android.util.TypedValue.COMPLEX_UNIT_SP);
          row.addView(b, lp);
        }
      }
      drnasEditKeyRows.requestLayout();
    } finally { drnasSizingKeys = false; }
    drnasRefreshPanels();
  }
  private void drnasSaveKeyOrder() {
    StringBuilder ids = new StringBuilder();
    for (Button b : drnasSmallKeys) {
      if (ids.length() > 0) ids.append(',');
      ids.append(drnasDefaultKeyOrder.indexOf(b));
    }
    drnasPrefs.edit().putString("keyboard_order", ids.toString()).apply();
  }
  private void drnasRestoreKeyOrder() {
    drnasDefaultKeyOrder.clear(); drnasDefaultKeyOrder.addAll(drnasSmallKeys);
    String saved = drnasPrefs.getString("keyboard_order", "");
    if (saved.isEmpty()) return;
    java.util.ArrayList<Button> order = new java.util.ArrayList<>();
    try {
      for (String part : saved.split(",")) {
        Button b = drnasDefaultKeyOrder.get(Integer.parseInt(part));
        if (order.contains(b)) return;
        order.add(b);
      }
      if (order.size() != drnasSmallKeys.size()) return;
      drnasSmallKeys.clear(); drnasSmallKeys.addAll(order);
    } catch (RuntimeException ignored) {}
  }
  private void drnasAttachGear(View content, boolean mouse) {
    DrnasPanel panel = drnasPanels.get(content); if (panel == null) return;
    FrameLayout.LayoutParams cp = (FrameLayout.LayoutParams)content.getLayoutParams();
    cp.topMargin = dpDrnas(27); content.setLayoutParams(cp);
    TextView gear = drnasUiLabel("⚙"); gear.setTextSize(18); gear.setAlpha(0.72f);
    gear.setGravity(Gravity.CENTER); gear.setBackground(drnasPill(Color.argb(190, 23, 42, 62)));
    gear.setContentDescription(mouse ? "Uredi miš i zoom" : "Uredi veličinu i raspored tipkovnice");
    FrameLayout.LayoutParams gp = new FrameLayout.LayoutParams(dpDrnas(34), dpDrnas(27), Gravity.TOP | Gravity.RIGHT);
    panel.host.addView(gear, gp);
    gear.setOnClickListener(v -> drnasOpenGroupEditor(mouse));
    panel.schedule();
  }
  private void drnasOpenGroupEditor(boolean mouse) {
    drnasReleaseAllInputs();
    if (drnasEditorPopup != null) drnasEditorPopup.dismiss();
    LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(dpDrnas(10), dpDrnas(6), dpDrnas(10), dpDrnas(8));
    root.setBackground(drnasPill(Color.argb(250, 15, 30, 47)));
    Button close = new Button(this); close.setAllCaps(false);
    close.setText((mouse ? "Miš i zoom" : "Tipkovnica i raspored") + "   ✕");
    drnasStyleKey(close, false); root.addView(close, new LinearLayout.LayoutParams(-1, dpDrnas(44)));
    android.widget.ScrollView scroller = new android.widget.ScrollView(this);
    LinearLayout rows = new LinearLayout(this); rows.setOrientation(LinearLayout.VERTICAL);
    scroller.addView(rows); root.addView(scroller, new LinearLayout.LayoutParams(-1, 0, 1));
    final String prefix = mouse ? "mouse" : "keyboard";
    drnasEditorSlider(rows, "Širina grupe", mouse ? 60 : 40, mouse ? 160 : 100,
        drnasPrefs.getInt(prefix + "_width", mouse ? 100 : 90), "%", value -> {
          drnasPrefs.edit().putInt(prefix + "_width", value).apply();
          if (mouse) drnasMouseButtonSizes(drnasMouseButtonPercent, false); else drnasKeyGeometry();
        });
    drnasEditorSlider(rows, "Visina grupe", 60, 220,
        drnasPrefs.getInt(prefix + "_height", 100), "%", value -> {
          drnasPrefs.edit().putInt(prefix + "_height", value).apply();
          if (mouse) drnasMouseButtonSizes(drnasMouseButtonPercent, false); else drnasKeyGeometry();
        });
    drnasOpacitySlider(rows, mouse);
    if (!mouse) {
      drnasEditorSlider(rows, "Broj redova", 1, 5, drnasPrefs.getInt("keyboard_rows", 2), "", value -> {
        drnasPrefs.edit().putInt("keyboard_rows", value).apply(); drnasKeyGeometry();
      });
      rows.addView(drnasUiLabel("Odaberi tipku i pomakni je u rasporedu"));
      android.widget.Spinner key = new android.widget.Spinner(this, android.widget.Spinner.MODE_DROPDOWN);
      java.util.ArrayList<String> labels = new java.util.ArrayList<>();
      for (Button b : drnasSmallKeys) labels.add(b.getText().toString().replace(" •", ""));
      android.widget.ArrayAdapter<String> adapter = new android.widget.ArrayAdapter<>(this, android.R.layout.simple_spinner_item, labels);
      adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item); key.setAdapter(adapter);
      key.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
        public void onNothingSelected(android.widget.AdapterView<?> p) {}
        public void onItemSelected(android.widget.AdapterView<?> p, View v, int pos, long id) {
          if (v instanceof TextView) ((TextView)v).setTextColor(drnasTextWhite);
        }
      });
      rows.addView(key, new LinearLayout.LayoutParams(-1, dpDrnas(46)));
      LinearLayout arrows = new LinearLayout(this);
      for (int direction : new int[] {-1, 1}) {
        Button move = new Button(this); move.setText(direction < 0 ? "← Ranije" : "Kasnije →"); move.setAllCaps(false); drnasStyleKey(move, false);
        arrows.addView(move, new LinearLayout.LayoutParams(0, dpDrnas(42), 1));
        move.setOnClickListener(v -> {
          int from = key.getSelectedItemPosition(), to = from + direction;
          if (from < 0 || to < 0 || to >= drnasSmallKeys.size()) return;
          java.util.Collections.swap(drnasSmallKeys, from, to);
          java.util.Collections.swap(labels, from, to); adapter.notifyDataSetChanged(); key.setSelection(to);
          drnasSaveKeyOrder(); drnasKeyGeometry();
        });
      }
      rows.addView(arrows);
      Button reset = new Button(this); reset.setText("Vrati izvorni raspored"); reset.setAllCaps(false); drnasStyleKey(reset, false);
      rows.addView(reset); reset.setOnClickListener(v -> {
        drnasSmallKeys.clear(); drnasSmallKeys.addAll(drnasDefaultKeyOrder);
        drnasPrefs.edit().remove("keyboard_order").putInt("keyboard_rows", 2).apply();
        drnasKeyGeometry(); drnasOpenGroupEditor(false);
      });
    }
    int width = Math.min(dpDrnas(340), getResources().getDisplayMetrics().widthPixels - dpDrnas(24));
    int height = Math.min(dpDrnas(mouse ? 330 : 480), getResources().getDisplayMetrics().heightPixels - dpDrnas(32));
    drnasEditorPopup = new android.widget.PopupWindow(root, width, height, true);
    drnasEditorPopup.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
    drnasEditorPopup.setOutsideTouchable(true); drnasEditorPopup.setElevation(dpDrnas(10));
    drnasEditorPopup.setInputMethodMode(android.widget.PopupWindow.INPUT_METHOD_NOT_NEEDED);
    drnasEditorPopup.showAtLocation(getWindow().getDecorView(), Gravity.TOP | Gravity.RIGHT, dpDrnas(12), dpDrnas(16));
    close.setOnClickListener(v -> drnasEditorPopup.dismiss());
  }
