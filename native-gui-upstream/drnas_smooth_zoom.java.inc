  private android.os.HandlerThread drnasZoomThread;
  private android.os.Handler drnasZoomWorker;
  private volatile boolean drnasSmoothZoomReady;
  private boolean drnasSmoothZoomEnabled = true;
  private java.io.File drnasZoomSignal, drnasZoomReady;
  private String drnasZoomSession;
  private double drnasZoomTotal;
  private long drnasZoomSequence;
  private boolean drnasZoomFlushPending;

  private void startDrnasSmoothZoom() {
    drnasSmoothZoomEnabled = getSharedPreferences("drnas_native_controls_v1", MODE_PRIVATE)
        .getBoolean("smooth_zoom", true);
    drnasZoomSignal = new java.io.File(getFilesDir(), "drnas-smooth-zoom-v3.signal");
    drnasZoomReady = new java.io.File(drnasZoomSignal.getPath() + ".ready");
    drnasZoomSession = java.util.UUID.randomUUID().toString();
    try {
      Os.setenv("DRNAS_SMOOTH_ZOOM_SIGNAL", drnasZoomSignal.getPath(), true);
      Os.setenv("DRNAS_SMOOTH_ZOOM_SESSION", drnasZoomSession, true);
    } catch (Exception e) { return; }
    drnasZoomThread = new android.os.HandlerThread("drnas-native-zoom-io");
    drnasZoomThread.start();
    drnasZoomWorker = new android.os.Handler(drnasZoomThread.getLooper());
    drnasZoomWorker.post(new Runnable() {
      public void run() {
        if (isDestroyed()) return;
        try {
          drnasSmoothZoomReady = java.nio.file.Files.readString(drnasZoomReady.toPath())
              .trim().equals(drnasZoomSession);
        } catch (Exception ignored) { drnasSmoothZoomReady = false; }
        if (!drnasSmoothZoomReady) drnasZoomWorker.postDelayed(this, 250);
      }
    });
  }

  private void drnasOfferZoom(float amount) {
    synchronized (this) {
      drnasZoomTotal += Math.max(-20f, Math.min(20f, amount));
      drnasZoomSequence++;
      if (drnasZoomFlushPending) return;
      drnasZoomFlushPending = true;
    }
    drnasZoomWorker.postDelayed(() -> {
      double total; long sequence;
      synchronized (BlenderActivity.this) {
        total = drnasZoomTotal; sequence = drnasZoomSequence;
        drnasZoomFlushPending = false;
      }
      try {
        android.util.AtomicFile file = new android.util.AtomicFile(drnasZoomSignal);
        java.io.FileOutputStream out = null;
        try {
          out = file.startWrite();
          out.write((drnasZoomSession + " " + sequence + " " + total + "\n")
              .getBytes(java.nio.charset.StandardCharsets.UTF_8));
          file.finishWrite(out);
        } catch (Exception e) { file.failWrite(out); throw e; }
      } catch (Exception e) { drnasSmoothZoomReady = false; }
    }, 16);
  }
