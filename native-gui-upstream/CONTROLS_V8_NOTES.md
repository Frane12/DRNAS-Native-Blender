# Native Blender Controls v8 TEST

Java/Python-only repack of the user-confirmed GPU v7 APK, Actions run 39562098774. Every native library and every bundled GPU driver must remain byte-identical. No native Blender compilation.

- Separate test install `hr.drnas.blendernativecontrolstest2026v8` because previous CI debug signing key is unavailable. Keep v7 installed; existing projects are not overwritten. Settings are separate.
- Small gear above the top-right of each group opens its editor. Gear opacity is independent of its group.
- Mouse/zoom and command-key groups have independent width, height and transparency controls. Keyboard size has its existing slider too. Every change persists and updates live.
- Command keys adapt to selected group dimensions and 1–5 rows. Pick a key and use Earlier/Later to reorder; reset restores original ordering. Actual button objects and their native input listeners are retained.
- Stretch screen checkbox expands the Android Vulkan window across available edge/cutout space and hides system bars. The existing native aspect-fit buffer is uniformly scaled to fill that window; resolution presets remain maximum bounds, not an exact forced 16:9 surface. No new native stretch mode or fabricated env flag.
- Init log: `Download/DRNAS/native-blender-init.log`, with one previous log kept. If shared-storage permission is missing, retain an app-private log and mirror it after permission is granted. Current path is shown in GPU settings.
- Log distinguishes requested driver, mapped shared library, first successful present, native loader messages and GPU vendor/renderer/version from Blender's actual context. Driver selection alone is not logged as successful activation.
- Init capture is bounded: native logcat 25 seconds/180 lines, mirror poll up to 60 seconds, Python GPU report one successful capture with at most 30 retries. No per-frame tracing or continuous performance overhead.
- Original save-before-exit, spring zoom, independent sizes, cursor and double-tap key latching remain.
- Original signed v7 APK/checksums are also copied to an unpublished GitHub draft for a durable native baseline.

CI verifies Java compilation, existing input/zoom/save tests, GPU init report behavior, APK identity/signature and byte-for-byte preservation of all native/driver binaries and original runtime members. Physical-device layout and cutout behavior require user testing.
