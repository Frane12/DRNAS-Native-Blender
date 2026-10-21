#!/usr/bin/env python3
"""Execute patched native size/input code with Android sysprops stubbed on host."""
import subprocess,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as d:
    d=Path(d);(d/'sys').mkdir()
    (d/'sys/system_properties.h').write_text('#define PROP_VALUE_MAX 92\ninline int __system_property_get(const char*, char*) {return 0;}\n')
    (d/'test.cc').write_text(r'''
#include <cassert>
#include "GHOST_AndroidMemoryTier.hh"
int main() {
 setenv("DRNAS_A810_RENDER_LIMIT","0",1);
 setenv("DRNAS_RENDER_OVERRIDE","1",1);
 setenv("DRNAS_RENDER_WIDTH","1280",1);setenv("DRNAS_RENDER_HEIGHT","720",1);
 int w,h;GHOST_android_drnas_a810_size(2400,1080,w,h);assert(w==1280 && h==576);
 GHOST_android_drnas_a810_size(1080,2400,w,h);assert(w==576 && h==1280);
 GHOST_android_drnas_a810_size(800,450,w,h);assert(w==800&&h==450);
 GHOST_android_drnas_touch_ratio_x().store(0.5f);GHOST_android_drnas_touch_ratio_y().store(0.4f);
 assert(ghost_android_scale_input_x(100)==50);assert(ghost_android_scale_input_y(100)==40);
 setenv("DRNAS_RENDER_WIDTH","0",1);setenv("DRNAS_RENDER_HEIGHT","0",1);
 GHOST_android_drnas_a810_size(2400,1080,w,h);assert(w==2400&&h==1080);
 setenv("DRNAS_RENDER_OVERRIDE","0",1);setenv("DRNAS_A810_RENDER_LIMIT","1",1);
 GHOST_android_drnas_a810_size(1920,1080,w,h);assert(w==960&&h==540);
}
''')
    subprocess.run(['g++','-std=c++17','-D__ANDROID__','-I'+str(d),'-I'+str(root/'intern/ghost/intern'),str(d/'test.cc'),'-o',str(d/'test')],check=True)
    subprocess.run([str(d/'test')],check=True)
print('PASS: executed native resolution, no-upscale, portrait, original A810 and XY touch mapping')
