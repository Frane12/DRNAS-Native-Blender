# SPDX-License-Identifier: GPL-2.0-or-later
"""App-private save request; acknowledge only a completed .blend save."""
import json
import os
import time
import bpy
from bpy.app.handlers import persistent

_path = os.environ.get('DRNAS_SMOOTH_ZOOM_SIGNAL', '')
_session = os.environ.get('DRNAS_SMOOTH_ZOOM_SESSION', '')
_seen = None
_pending = None
_browser_seen = False
_browser_started = 0.0
_old_display = None


def _restore_browser():
    global _old_display
    if _old_display is not None:
        bpy.context.preferences.view.filebrowser_display_type = _old_display
        _old_display = None


def _reply(token, state, message=''):
    payload = dict(session=_session, token=token, state=state, message=message)
    target = _path + '.exit-result'
    with open(target + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    os.replace(target + '.tmp', target)


def _finish(state, message=''):
    global _pending
    token, _pending = _pending, None
    _restore_browser()
    if token:
        _reply(token, state, message)


@persistent
def _saved(_unused):
    # save_post runs after Blender's file writer reports success.
    if _pending:
        path = bpy.data.filepath
        if path and os.path.isfile(path) and os.path.getsize(path) > 0:
            _finish('SAVED')


def _begin_save(token):
    global _pending, _browser_seen, _browser_started, _old_display
    _pending, _browser_seen, _browser_started = token, False, time.monotonic()
    try:
        if bpy.data.filepath:
            result = bpy.ops.wm.save_mainfile('EXEC_DEFAULT')
            if _pending:
                if 'FINISHED' in result:
                    _saved(None)
                    if _pending:
                        _finish('ERROR', 'Datoteka nije potvrđena nakon spremanja.')
                else:
                    _finish('ERROR', 'Blender nije dovršio spremanje.')
        else:
            # Android GHOST has one native surface: use a temporary full-screen
            # editor, never request a second OS window for Save As.
            _old_display = bpy.context.preferences.view.filebrowser_display_type
            bpy.context.preferences.view.filebrowser_display_type = 'SCREEN'
            window = bpy.context.window or next(iter(bpy.context.window_manager.windows), None)
            if window is None or not window.screen.areas:
                raise RuntimeError('Blender prozor još nije spreman.')
            area = max(window.screen.areas, key=lambda a: a.width * a.height)
            with bpy.context.temp_override(window=window, area=area):
                result = bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
            if 'CANCELLED' in result:
                _finish('CANCELLED', 'Spremanje je otkazano.')
    except Exception as error:
        _finish('ERROR', str(error))


def _tick():
    global _seen, _browser_seen
    try:
        try:
            with open(_path + '.exit-command', encoding='utf-8') as f:
                command = json.load(f)
        except (OSError, ValueError):
            command = {}
        identity = (command.get('token'), command.get('action'))
        if command.get('session') == _session and identity != _seen:
            _seen = identity
            if command.get('action') == 'SAVE':
                _begin_save(command['token'])
            elif command.get('action') == 'CANCEL' and _pending == command.get('token'):
                _finish('CANCELLED', 'Spremanje je otkazano.')
        if _pending and not bpy.data.filepath:
            areas = [a for w in bpy.context.window_manager.windows for a in w.screen.areas]
            browser_open = any(a.type == 'FILE_BROWSER' for a in areas)
            _browser_seen |= browser_open
            if not browser_open and (_browser_seen or time.monotonic() - _browser_started > 5):
                _finish('CANCELLED', 'Spremanje je otkazano ili preglednik nije otvoren.')
    except Exception:
        # Never acknowledge success on an unexpected error.
        if _pending:
            _finish('ERROR', 'Spremanje nije potvrđeno.')
    return 0.15


def register():
    if _path and _session:
        if _saved not in bpy.app.handlers.save_post:
            bpy.app.handlers.save_post.append(_saved)
        if not bpy.app.timers.is_registered(_tick):
            bpy.app.timers.register(_tick, first_interval=0.25, persistent=True)


def unregister():
    if _saved in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(_saved)
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    _restore_browser()
