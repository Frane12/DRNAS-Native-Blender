#!/usr/bin/env python3
import pathlib,runpy,sys,tempfile,types,unittest,os
from unittest.mock import patch
class InitReport(unittest.TestCase):
 def load(self,root,window=True):
  timer=[]
  bpy=types.SimpleNamespace(context=types.SimpleNamespace(window=types.SimpleNamespace(width=1280,height=576) if window else None,window_manager=types.SimpleNamespace(windows=[])),app=types.SimpleNamespace(version_string='5.3',timers=types.SimpleNamespace(register=lambda f,**kwargs:timer.append(f))))
  platform=types.SimpleNamespace(backend_type_get=lambda:'VULKAN',vendor_get=lambda:'Mesa',renderer_get=lambda:'Adreno 840',version_get=lambda:'Mesa test')
  with patch.dict(sys.modules,{'bpy':bpy,'gpu':types.SimpleNamespace(platform=platform)}),patch.dict(os.environ,{'DRNAS_INIT_LOG':str(root/'init.log')}):
   mod=runpy.run_path(str(pathlib.Path(__file__).with_name('drnas_native_gpu_init.py')))
  return timer[0],bpy
 def test_context_report_once(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);f,b=self.load(root)
   with patch.dict(os.environ,{'DRNAS_INIT_LOG':str(root/'init.log')}):
    self.assertIsNone(f());original=(root/'init.log').read_text();self.assertIsNone(f())
   self.assertIn('renderer=Adreno 840',original);self.assertIn('backend=VULKAN',original)
   self.assertEqual(original,(root/'init.log').read_text())
 def test_no_context_no_success_claim(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);f,b=self.load(root,False)
   with patch.dict(os.environ,{'DRNAS_INIT_LOG':str(root/'init.log')}):self.assertEqual(f(),1.0)
   self.assertFalse((root/'init.log').exists())
 def test_retry_is_bounded(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);f,b=self.load(root,False)
   with patch.dict(os.environ,{'DRNAS_INIT_LOG':str(root/'init.log')}):
    for _ in range(29):self.assertEqual(f(),1.0)
    self.assertIsNone(f())
if __name__=='__main__':unittest.main()
