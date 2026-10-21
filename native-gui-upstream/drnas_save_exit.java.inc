  private volatile String drnasSaveExitToken;

  private void drnasSaveAndExit() {
    if (drnasZoomWorker == null || drnasZoomSignal == null) {
      android.widget.Toast.makeText(this, "Spremanje još nije spremno. Pokušaj ponovno.", android.widget.Toast.LENGTH_LONG).show();
      return;
    }
    drnasStopSpringZoom();
    drnasSendInput(3, 0, 0, 0); drnasSendInput(5, 0, 0, 0);
    final String token = java.util.UUID.randomUUID().toString();
    drnasSaveExitToken = token;
    android.widget.Toast.makeText(this, "Spremanje projekta… Za novi projekt odaberi naziv i lokaciju u Blenderu.", android.widget.Toast.LENGTH_LONG).show();
    drnasZoomWorker.post(() -> {
      if (drnasWriteExitRequest(token, "SAVE")) drnasPollSaveExit(token);
    });
  }

  private boolean drnasWriteExitRequest(String token, String action) {
    try {
      org.json.JSONObject command = new org.json.JSONObject();
      command.put("session", drnasZoomSession); command.put("token", token); command.put("action", action);
      android.util.AtomicFile file = new android.util.AtomicFile(new java.io.File(drnasZoomSignal.getPath() + ".exit-command"));
      java.io.FileOutputStream out = null;
      try {
        out = file.startWrite(); out.write(command.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        file.finishWrite(out);
      } catch (Exception e) { file.failWrite(out); throw e; }
      return true;
    } catch (Exception e) {
      runOnUiThread(() -> {
        if (token.equals(drnasSaveExitToken)) drnasSaveExitToken = null;
        android.widget.Toast.makeText(this, "Spremanje nije pokrenuto. Aplikacija ostaje otvorena.", android.widget.Toast.LENGTH_LONG).show();
      });
      return false;
    }
  }

  private void drnasPollSaveExit(final String token) {
    if (!token.equals(drnasSaveExitToken) || isDestroyed()) return;
    try {
      java.io.File result = new java.io.File(drnasZoomSignal.getPath() + ".exit-result");
      org.json.JSONObject reply = new org.json.JSONObject(new String(java.nio.file.Files.readAllBytes(result.toPath()), java.nio.charset.StandardCharsets.UTF_8));
      if (drnasZoomSession.equals(reply.optString("session")) && token.equals(reply.optString("token"))) {
        String state = reply.optString("state");
        if ("SAVED".equals(state)) {
          runOnUiThread(() -> { if (token.equals(drnasSaveExitToken)) exitDrnasBlender(); });
          return;
        }
        if ("ERROR".equals(state) || "CANCELLED".equals(state)) {
          final String message = reply.optString("message", "Spremanje nije dovršeno.");
          runOnUiThread(() -> {
            if (!token.equals(drnasSaveExitToken)) return;
            drnasSaveExitToken = null;
            android.widget.Toast.makeText(this, message + " Aplikacija ostaje otvorena.", android.widget.Toast.LENGTH_LONG).show();
          });
          return;
        }
      }
    } catch (Exception ignored) {}
    // Waiting is never treated as successful saving. No timeout can kill Blender.
    drnasZoomWorker.postDelayed(() -> drnasPollSaveExit(token), 180);
  }
