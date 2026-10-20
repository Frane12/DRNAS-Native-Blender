# DRNAS Native Blender — REAL viewport upstream adoption LAB

## Scope and source attribution

This experimental branch creates a **separately installed APK** with an actual
native Blender UI and 3D viewport by **repackaging a pinned third-party open
source Android Blender build**, not by claiming that the DRNAS 4.5.4 headless
Blender build has acquired a window backend.

Upstream: [simfeo/blender](https://github.com/simfeo/blender),
tag `android-alpha-4`, commit `d93bd33cba768e19ee4387a31c0ea137ee2f0047`.
Prebuilt base is the upstream `blender-lite.apk` released 26 September 2026,
size 203,199,511 bytes; SHA-256
`5d05835e52377c7d987145b6c35a944804c88e32e114fd53ede4c36edea20ce1`.
The source is available at that exact upstream tag. Blender is GPL licensed.
**This is an unofficial experimental derivative, not an official Blender build.**
Use only with the license notices and corresponding upstream source supplied.

## What's new compared with existing DRNAS native LAB

- Full native Vulkan Blender UI and live 3D viewport **from the upstream binary**.
- DRNAS mini overlay, collapsible, shortcut buttons `G`, `R`, `S`, `ESC`.
- These shortcuts use the upstream GHOST JNI key queue directly. They are not
  synthetic mouse actions. Touch/orbit come from upstream Android GHOST.
- Distinct package `hr.drnas.nativeblendergui` to avoid overwriting EmuDRNAS,
  the Vulkan LAB, GHOST Input LAB, and a stock upstream Blender installation.
- JNI native libraries + runtime assets are repackaged from the pinned APK;
  the corresponding Java Activity is patched from the **matching GPL source**.
- GitHub CI verifies APK integrity and checks the output with `apksigner`.

## What this DOES NOT do (yet)

- Does **not** compile Blender 4.5.4 with Android GHOST/Vulkan.
- Does **not** implement DRNAS LMB/RMB/Zoom overlays. These require real
  native input plumbing in the Blender source; they must not be faked.
- Does **not** mean runtime success on every GPU. A device install/launch and
  viewport test is still required.
- Debug signing; **do not release as a stable APK**.
- First run may take a long time as Python/scripts are unpacked by upstream
  Activity. Do not delete app data during initialization.

## GUI follow-up

For a fully independent DRNAS GUI port, integrate SDL3 GHOST / Vulkan into
our existing headless ARM64 build, or build Blender from the upstream Android
source tag with our DRNAS input overlay wired into native GHOST, then validate
viewport drawing, touch focus and render on Adreno 840 / Mali / Xclipse.
The current adoption LAB enables immediate real-viewport testing in parallel.
