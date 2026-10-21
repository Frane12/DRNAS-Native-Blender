# SPDX-License-Identifier: GPL-2.0-or-later
"""Android zoom signal -> eased logarithmic 3D view distance. No wheel events."""
import math
import os
import time
import bpy

_path = os.environ.get('DRNAS_SMOOTH_ZOOM_SIGNAL', '')
_session = os.environ.get('DRNAS_SMOOTH_ZOOM_SESSION', '')
_sequence = -1
_total = 0.0
_region = None
_target = None
_last_applied = None
_last_time = 0.0
_announced = False


def ease_distance(current, target, dt):
    """Frame-rate independent easing in log space (scale-proportional zoom)."""
    a = 1.0 - math.exp(-max(0.0, min(dt, 0.1)) / 0.065)
    return math.exp(math.log(max(1e-6, current)) * (1-a) + math.log(max(1e-6, target)) * a)


def _viewport():
    window = bpy.context.window
    if window is None:
        manager = bpy.context.window_manager
        window = next(iter(manager.windows), None) if manager else None
    if window is None or window.screen is None:
        return None, None
    areas = [a for a in window.screen.areas if a.type == 'VIEW_3D']
    if not areas:
        return None, None
    area = max(areas, key=lambda a: a.width * a.height)
    return area, area.spaces.active.region_3d


def _tick():
    global _sequence, _total, _region, _target, _last_applied, _last_time, _announced
    try:
        if not _announced:
            with open(_path + '.ready', 'w', encoding='utf-8') as f:
                f.write(_session)
            _announced = True
        now = time.monotonic()
        dt = min(0.1, max(0.001, now - _last_time)) if _last_time else 1/60
        _last_time = now
        delta = 0.0
        stop = False
        try:
            with open(_path, encoding='utf-8') as f:
                parts = f.read(256).split()
            session, sequence, total = parts[:3]
            sequence, total = int(sequence), float(total)
            if session == _session and sequence != _sequence and math.isfinite(total):
                delta = max(-40.0, min(40.0, total - _total))
                _sequence, _total = sequence, total
                stop = len(parts) > 3 and parts[3] == 'STOP'
        except (OSError, ValueError):
            pass
        area, region = _viewport()
        if region is None:
            _region = _target = _last_applied = None
            return 0.1
        current = max(1e-6, float(region.view_distance))
        identity = region.as_pointer()
        # A scene load, editor change or a manual pinch/orbit must not snap
        # back to the old target. Start the next slider movement from here.
        if identity != _region or _target is None or (_last_applied is not None
                and abs(math.log(current / max(1e-6, _last_applied))) > 0.002):
            _region, _target = identity, current
        if stop:
            _target, delta = current, 0.0
        if delta:
            _target = max(1e-6, min(1e12, _target * math.exp(-delta * 0.11)))
        moving = abs(math.log(current / _target)) > 0.0001
        if moving:
            region.view_distance = ease_distance(current, _target, dt)
            _last_applied = float(region.view_distance)
            area.tag_redraw()
        else:
            if current != _target:
                region.view_distance = _target
                area.tag_redraw()
            _last_applied = float(region.view_distance)
        return 1/60 if moving or delta else 1/30
    except Exception:
        _region = _target = _last_applied = None
        return 0.25


def register():
    if _path and _session and not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=0.1, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
