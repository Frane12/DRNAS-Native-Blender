"""One startup GPU report from Blender's actual active graphics context."""
import os
from datetime import datetime
import bpy
import gpu

_attempts = 0
_done = False

def _report():
    global _attempts, _done
    if _done:
        return None
    _attempts += 1
    path = os.environ.get('DRNAS_INIT_LOG')
    if not path:
        return None
    try:
        window = bpy.context.window
        if window is None:
            window = next(iter(bpy.context.window_manager.windows), None)
        if window is None:
            return 1.0 if _attempts < 30 else None
        details = {
            'backend': gpu.platform.backend_type_get(),
            'vendor': gpu.platform.vendor_get(),
            'renderer': gpu.platform.renderer_get(),
            'version': gpu.platform.version_get(),
            'window': f'{window.width}x{window.height}',
            'blender': bpy.app.version_string,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as log:
            log.write('ACTIVE_GPU_CONTEXT ' + datetime.now().isoformat() + '\n')
            for key, value in details.items():
                log.write(f'  {key}={value}\n')
        _done = True
        return None
    except Exception as error:
        if _attempts < 30:
            return 1.0
        try:
            with open(path, 'a', encoding='utf-8') as log:
                log.write('GPU_CONTEXT_REPORT_FAILED ' + type(error).__name__ + '\n')
        except OSError:
            pass
        return None

bpy.app.timers.register(_report, first_interval=1.0, persistent=True)
