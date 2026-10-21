#!/usr/bin/env python3
"""One split-touch host in relative mode, fixed settings close header, rate zoom."""
from pathlib import Path
import sys

java = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender'
p = java / 'BlenderActivity.java'
s = p.read_text()

def once(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new, 1)

once('  private View drnasMousePad;', '  private View drnasMousePad;\n  private FrameLayout drnasMouseRoot;')
once('      drnasMousePad = new View(this);', '''      drnasMouseRoot = new FrameLayout(this);
      drnasMouseRoot.setMotionEventSplittingEnabled(true);
      drnasMouseRoot.setSystemUiVisibility(decor.getSystemUiVisibility());
      drnasMousePad = new View(this);
      drnasMouseRoot.addView(drnasMousePad, new FrameLayout.LayoutParams(-1, -1));''')
once('new android.widget.PopupWindow(drnasMousePad, -1, -1, false)',
     'new android.widget.PopupWindow(drnasMouseRoot, -1, -1, false)')
once('      host = new FrameLayout(BlenderActivity.this);',
     '      host = new FrameLayout(BlenderActivity.this);\n      host.setMotionEventSplittingEnabled(true);')
once('        popup.dismiss();\n        return;', '        host.setVisibility(View.GONE);\n        popup.dismiss();\n        return;')
once('      if (!popup.isShowing()) {\n        popup.setWidth(width);', '''      host.setVisibility(View.VISIBLE);
      if (drnasRelativeMouse && drnasMouseRoot != null) {
        // All fingers belong to one ViewRoot. Each child keeps its own pointer
        // stream, so a finger on LMB never becomes a two-finger zoom gesture.
        popup.dismiss();
        popup.setContentView(null);
        if (host.getParent() != drnasMouseRoot) {
          if (host.getParent() instanceof ViewGroup) ((ViewGroup)host.getParent()).removeView(host);
          drnasMouseRoot.addView(host);
        }
        FrameLayout.LayoutParams panelPosition = new FrameLayout.LayoutParams(width, height);
        panelPosition.leftMargin = x; panelPosition.topMargin = y;
        host.setLayoutParams(panelPosition);
      } else if (!popup.isShowing()) {
        if (host.getParent() instanceof ViewGroup) ((ViewGroup)host.getParent()).removeView(host);
        popup.setContentView(host);
        popup.setWidth(width);''')

# Close remains visible while the options content scrolls underneath it.
once('''    final android.widget.ScrollView options = new android.widget.ScrollView(this);
    final LinearLayout optionRows = new LinearLayout(this);
    options.addView(optionRows);
    options.setFillViewport(false);''', '''    final LinearLayout options = new LinearLayout(this);
    options.setOrientation(LinearLayout.VERTICAL);
    options.setBackground(drnasPill(Color.argb(248, 15, 30, 47)));
    final Button closeOptions = new Button(this);
    closeOptions.setText("Zatvori postavke  ✕");
    closeOptions.setAllCaps(false);
    closeOptions.setContentDescription("Zatvori postavke i vrati se Blenderu");
    closeOptions.setOnClickListener(v -> drnasPanelVisibility(options, View.GONE));
    options.addView(closeOptions, new LinearLayout.LayoutParams(-1, dpDrnas(46)));
    final android.widget.ScrollView optionScroll = new android.widget.ScrollView(this);
    final LinearLayout optionRows = new LinearLayout(this);
    optionScroll.addView(optionRows);
    options.addView(optionScroll, new LinearLayout.LayoutParams(-1, 0, 1));
    drnasOptionsPanel = options;''')
once('  private void showDrnasExitDialog() {', '''  private View drnasOptionsPanel;
  private void showDrnasExitDialog() {
    if (drnasOptionsPanel != null && drnasOptionsPanel.getVisibility() == View.VISIBLE) {
      drnasPanelVisibility(drnasOptionsPanel, View.GONE);
      return;
    }''')
once('EDIT: pomakni panel prstom, DONE: spremi položaj', 'Ručkicom ⠿ pomakni kontrole; položaj se sprema automatski')

# Replace distance-per-move with frame-driven velocity while held away from center.
a = s.index('    zoom.setOnSeekBarChangeListener(')
b = s.index('    zoom.setOnTouchListener(', a)
s = s[:a] + '''    zoom.setContentDescription("Feder zoom: odmak od sredine određuje brzinu, otpusti za stop");
    zoom.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
      public void onProgressChanged(SeekBar bar, int progress, boolean byUser) {
        if (byUser && !drnasEdit) drnasSpring.update(progress);
      }
      public void onStartTrackingTouch(SeekBar bar) {
        if (drnasEdit) return;
        drnasSpring.begin(bar.getProgress());
        drnasSpringLastFrame = 0;
        android.view.Choreographer.getInstance().removeFrameCallback(drnasSpringFrame);
        android.view.Choreographer.getInstance().postFrameCallback(drnasSpringFrame);
      }
      public void onStopTrackingTouch(SeekBar bar) {
        drnasStopSpringZoom();
        bar.setProgress(50); drnasZoomPrevious = 50;
      }
    });
''' + s[b:]
once('    zoom.setOnTouchListener((v, event) -> {', '''    zoom.setOnTouchListener((v, event) -> {
      if (event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
        drnasStopSpringZoom(); zoom.setProgress(50);
      }''')
once('    drnasWindowsActive = false;\n    drnasHidePanels();\n    super.onPause();',
     '    drnasStopSpringZoom();\n    drnasWindowsActive = false;\n    drnasHidePanels();\n    super.onPause();')
once('  private void requestAllFilesAccess() {', '''  private final DrnasZoomSpring drnasSpring = new DrnasZoomSpring();
  private long drnasSpringLastFrame;
  private final android.view.Choreographer.FrameCallback drnasSpringFrame = new android.view.Choreographer.FrameCallback() {
    public void doFrame(long now) {
      if (!drnasSpring.isTracking() || !drnasWindowsActive) return;
      double dt = drnasSpringLastFrame == 0 ? 1.0 / 60 : (now - drnasSpringLastFrame) / 1e9;
      drnasSpringLastFrame = now;
      float amount = (float)drnasSpring.advance(dt);
      if (amount != 0) drnasSendInput(6, 0, 0, amount);
      android.view.Choreographer.getInstance().postFrameCallback(this);
    }
  };
  private void drnasStopSpringZoom() {
    drnasSpring.release();
    android.view.Choreographer.getInstance().removeFrameCallback(drnasSpringFrame);
    if (drnasSmoothZoomReady && drnasZoomWorker != null) {
      synchronized (this) { drnasZoomStopRequested = true; }
      drnasOfferZoom(0);
    }
  }

  private void requestAllFilesAccess() {''')
once('  private boolean drnasZoomFlushPending;',
     '  private boolean drnasZoomFlushPending;\n  private boolean drnasZoomStopRequested;')
once('      drnasZoomTotal +=', '      if (amount != 0) drnasZoomStopRequested = false;\n      drnasZoomTotal +=')
once('      double total; long sequence;', '      double total; long sequence; boolean stop;')
once('        total = drnasZoomTotal; sequence = drnasZoomSequence;',
     '        total = drnasZoomTotal; sequence = drnasZoomSequence; stop = drnasZoomStopRequested;')
once('sequence + " " + total + "\\n"', 'sequence + " " + total + " " + (stop ? "STOP" : "RUN") + "\\n"')
once('java.nio.file.Files.readString(drnasZoomReady.toPath())',
     'new String(java.nio.file.Files.readAllBytes(drnasZoomReady.toPath()), java.nio.charset.StandardCharsets.UTF_8)')
p.write_text(s)
(java / 'DrnasZoomSpring.java').write_text(Path(__file__).with_name('DrnasZoomSpring.java').read_text())
print('PASS: unified relative split-touch surface; fixed settings Close/Back; frame-driven spring zoom')
