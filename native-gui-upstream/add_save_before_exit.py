#!/usr/bin/env python3
"""Android Back -> explicit save/discard/cancel; kill only after save success."""
from pathlib import Path
import sys

p = Path(sys.argv[1]) / 'build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java'
s = p.read_text()
old = '''        .setTitle("Exit Native Blender?")
        .setMessage("Unsaved Blender changes will be lost. Close the application?")
        .setNegativeButton("Stay", (dialog, which) -> {})
        .setPositiveButton("Exit", (dialog, which) -> exitDrnasBlender())'''
assert s.count(old) == 1
s = s.replace(old, '''        .setTitle("Spremiti projekt prije izlaska?")
        .setMessage("Spremi i zatvori aplikaciju ili izađi bez spremanja promjena.")
        .setNegativeButton("Odustani", (dialog, which) -> {})
        .setNeutralButton("Bez spremanja", (dialog, which) -> exitDrnasBlender())
        .setPositiveButton("Spremi i izađi", (dialog, which) -> drnasSaveAndExit())''')
anchor = '    if (drnasExitDialogOpen || drnasExitRequested || isFinishing()) return;'
assert s.count(anchor) == 1
s = s.replace(anchor, '''    if (drnasSaveExitToken != null) {
      String cancel = drnasSaveExitToken;
      drnasSaveExitToken = null;
      // Back cancels a pending native Save As browser and leaves Blender open.
      nativeOnKey(KeyEvent.KEYCODE_ESCAPE, KeyEvent.ACTION_DOWN, 0);
      nativeOnKey(KeyEvent.KEYCODE_ESCAPE, KeyEvent.ACTION_UP, 0);
      drnasZoomWorker.post(() -> drnasWriteExitRequest(cancel, "CANCEL"));
      android.widget.Toast.makeText(this, "Spremanje otkazano. Aplikacija ostaje otvorena.", android.widget.Toast.LENGTH_SHORT).show();
      return;
    }
''' + anchor)
anchor = '    drnasExitRequested = true;'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\n    drnasStopSpringZoom();\n    drnasSaveExitToken = null;')
anchor = '  private void requestAllFilesAccess() {'
assert s.count(anchor) == 1
s = s.replace(anchor, Path(__file__).with_name('drnas_save_exit.java.inc').read_text() + '\n' + anchor)
p.write_text(s)
print('PASS: Back offers Save and Exit / Discard / Cancel; save success gates shutdown')
