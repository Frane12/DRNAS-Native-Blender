#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?upstream source path required}"
PATCH="$(cd "$(dirname "$0")" && pwd)"
python3 "$PATCH/patch_native_ghost.py" "$ROOT"
python3 "$PATCH/create_sdl3_gui_preview.py" "$ROOT/build_files/android/apk"
python3 "$PATCH/add_drnas_controls.py" "$ROOT/build_files/android/apk"
python3 "$PATCH/patch_shortcut_ui_native.py" "$ROOT"
python3 "$PATCH/add_shortcuts_ui_scaling.py" "$ROOT"
python3 "$PATCH/patch_adreno810_resolution.py" "$ROOT"
python3 "$PATCH/fix_nested_host_tools.py" "$ROOT"
for script in add_drnas_splash add_adreno810_autoprofile set_pre_alpha_app_identity patch_release_exit_no_log fix_native_control_windows add_emu_control_options polish_controls_smooth_zoom fix_multitouch_spring_settings polish_cursor_button_style add_save_before_exit add_independent_sizes_input_latch add_gpu_driver_options; do
  python3 "$PATCH/$script.py" "$ROOT"
done
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/'build_files/android/apk/app/src/main/AndroidManifest.xml'
s=p.read_text().replace('package="org.blender.blender"','package="hr.drnas.blendernativegputest2026v7"')
s=s.replace('android:versionCode="1"','android:versionCode="8"').replace('android:versionName="0.1.0"','android:versionName="0.1.7-gpu-resolution-test"').replace('Native Blender PreAlpha 0.1','Native Blender GPU TEST')
p.write_text(s)
PY
