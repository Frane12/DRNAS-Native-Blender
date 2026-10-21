"""Behavior tests for startup zoom without requiring a Blender rebuild."""
import importlib.util
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class Region:
    def __init__(self, distance=10):
        self.view_distance = distance
    def as_pointer(self):
        return id(self)


class SmoothZoomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'zoom.signal')
        self.region = Region()
        self.area = SimpleNamespace(type='VIEW_3D', width=900, height=500,
            spaces=SimpleNamespace(active=SimpleNamespace(region_3d=self.region)), tag_redraw=lambda: None)
        window = SimpleNamespace(screen=SimpleNamespace(areas=[self.area]))
        fake = SimpleNamespace(context=SimpleNamespace(window=None,
            window_manager=SimpleNamespace(windows=[window])))
        with patch.dict(sys.modules, bpy=fake), patch.dict(os.environ,
                DRNAS_SMOOTH_ZOOM_SIGNAL=self.path, DRNAS_SMOOTH_ZOOM_SESSION='session'):
            spec = importlib.util.spec_from_file_location('zoom_under_test',
                Path(__file__).with_name('drnas_native_smooth_zoom.py'))
            self.zoom = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.zoom)
        self.now = 1.0
        self.step()

    def step(self, dt=1/60):
        self.now += dt
        with patch.object(self.zoom.time, 'monotonic', return_value=self.now):
            self.zoom._tick()

    def signal(self, sequence, total, session='session'):
        Path(self.path).write_text(f'{session} {sequence} {total}')

    def test_continuous_zoom_converges_without_wheel_steps_or_replay(self):
        self.signal(1, 1)
        values = []
        for _ in range(50):
            self.step()
            values.append(self.region.view_distance)
        target = 10 * math.exp(-0.11)
        self.assertGreater(values[0], target)
        self.assertLess(values[0], 10)
        self.assertGreater(len(set(values)), 20)
        self.assertAlmostEqual(values[-1], target, places=3)
        for _ in range(10): self.step()
        self.assertAlmostEqual(self.region.view_distance, target, places=3)

    def test_manual_pinch_is_preserved_and_next_delta_starts_there(self):
        self.signal(1, 2)
        for _ in range(50): self.step()
        self.region.view_distance = 30
        self.step()
        self.assertEqual(self.region.view_distance, 30)
        self.signal(2, 3)
        for _ in range(50): self.step()
        self.assertAlmostEqual(self.region.view_distance, 30 * math.exp(-0.11), places=2)

    def test_new_scene_and_stale_session_do_not_replay_old_zoom(self):
        self.signal(1, 4)
        for _ in range(50): self.step()
        replacement = Region(40)
        self.area.spaces.active.region_3d = replacement
        self.step()
        self.assertEqual(replacement.view_distance, 40)
        self.signal(100, 500, 'stale-session')
        self.step()
        self.assertEqual(replacement.view_distance, 40)

    def test_easing_is_frame_rate_independent(self):
        distance = 10
        for _ in range(4): distance = self.zoom.ease_distance(distance, 5, 1/60)
        self.assertAlmostEqual(distance, self.zoom.ease_distance(10, 5, 1/15))

    def test_spring_release_stops_in_flight_easing_immediately(self):
        self.signal(1, 8)
        self.step()
        stopped_distance = self.region.view_distance
        Path(self.path).write_text('session 2 8 STOP')
        for _ in range(20): self.step()
        self.assertEqual(self.region.view_distance, stopped_distance)
        Path(self.path).write_text('session 3 9 RUN')
        self.step()
        self.assertLess(self.region.view_distance, stopped_distance)


if __name__ == '__main__':
    unittest.main()
