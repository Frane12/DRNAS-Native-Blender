"""Verify save completion, failure and cancellation cannot be confused."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import nullcontext


class SaveExitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.signal = self.root / 'signal'
        self.project = self.root / 'project.blend'
        self.project.write_bytes(b'BLENDER-test-completed-file')
        self.area = SimpleNamespace(type='VIEW_3D', width=900, height=500)
        window = SimpleNamespace(screen=SimpleNamespace(areas=[self.area]))
        self.preferences = SimpleNamespace(view=SimpleNamespace(filebrowser_display_type='WINDOW'))
        self.data = SimpleNamespace(filepath=str(self.project))
        self.wm = SimpleNamespace(save_mainfile=lambda *a: {'FINISHED'},
                                  save_as_mainfile=lambda *a: {'RUNNING_MODAL'})
        bpy = ModuleType('bpy')
        bpy.context = SimpleNamespace(window=window, window_manager=SimpleNamespace(windows=[window]),
            preferences=self.preferences, temp_override=lambda **kwargs: nullcontext())
        bpy.data = self.data
        bpy.ops = SimpleNamespace(wm=self.wm)
        app = ModuleType('bpy.app')
        handlers = ModuleType('bpy.app.handlers')
        handlers.persistent = lambda function: function
        handlers.save_post = []
        app.handlers = handlers
        bpy.app = app
        with patch.dict(sys.modules, {'bpy': bpy, 'bpy.app': app, 'bpy.app.handlers': handlers}), \
             patch.dict(os.environ, DRNAS_SMOOTH_ZOOM_SIGNAL=str(self.signal), DRNAS_SMOOTH_ZOOM_SESSION='test'):
            spec = importlib.util.spec_from_file_location('exit_under_test', Path(__file__).with_name('drnas_native_save_exit.py'))
            self.exit = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.exit)

    def result(self):
        return json.loads(Path(str(self.signal) + '.exit-result').read_text())

    def test_existing_project_success_is_acknowledged(self):
        self.exit._begin_save('request')
        self.assertEqual(self.result()['state'], 'SAVED')
        self.assertEqual(self.result()['token'], 'request')

    def test_failed_write_never_reports_success(self):
        def fail(*args): raise RuntimeError('Disk full')
        self.wm.save_mainfile = fail
        self.exit._begin_save('request')
        self.assertEqual(self.result()['state'], 'ERROR')

    def test_cancelled_operator_never_reports_success(self):
        self.wm.save_mainfile = lambda *args: {'CANCELLED'}
        self.exit._begin_save('request')
        self.assertNotEqual(self.result()['state'], 'SAVED')

    def test_missing_output_is_not_a_completed_save(self):
        self.project.unlink()
        self.exit._begin_save('request')
        self.assertEqual(self.result()['state'], 'ERROR')

    def test_new_project_waits_for_save_post_and_restores_browser(self):
        self.data.filepath = ''
        self.exit._begin_save('request')
        self.assertEqual(self.preferences.view.filebrowser_display_type, 'SCREEN')
        self.assertFalse(Path(str(self.signal) + '.exit-result').exists())
        self.data.filepath = str(self.project)
        self.exit._saved(None)
        self.assertEqual(self.result()['state'], 'SAVED')
        self.assertEqual(self.preferences.view.filebrowser_display_type, 'WINDOW')

    def test_cancelled_browser_leaves_project_open(self):
        self.data.filepath = ''
        self.exit._begin_save('request')
        self.area.type = 'FILE_BROWSER'
        self.exit._tick()
        self.area.type = 'VIEW_3D'
        self.exit._tick()
        self.assertEqual(self.result()['state'], 'CANCELLED')
        self.assertEqual(self.preferences.view.filebrowser_display_type, 'WINDOW')

    def test_previous_process_command_is_ignored(self):
        Path(str(self.signal) + '.exit-command').write_text(json.dumps(dict(session='old', token='old-request', action='SAVE')))
        self.exit._tick()
        self.assertIsNone(self.exit._pending)
        self.assertFalse(Path(str(self.signal) + '.exit-result').exists())


if __name__ == '__main__':
    unittest.main()
