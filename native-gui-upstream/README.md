# Native Blender PreAlpha 0.1 — Android ARM64

**Unofficial experimental native Android Blender build**, based on the
[specific simfeo/blender Android port source](https://github.com/simfeo/blender/tree/d93bd33cba768e19ee4387a31c0ea137ee2f0047)
(commit `d93bd33cba768e19ee4387a31c0ea137ee2f0047`) with separately
maintained DRNAS JNI/GHOST, input and Android overlay patches in this repository.
This is **not an official Blender Foundation release** and is **not the
separate DRNAS emulation-based Blender project**.

## What you can test

- Native ARM64 `libblender.so`, native Blender GUI / Vulkan viewport;
  the CI workflow compiles the upstream **lite** Android target.
- Blender scene editing, touchscreen, native LMB/RMB, zoom and adjustable
  floating touch controls, keyboard shortcuts and GUI scaling.
- Automatic Adreno 810 device profile (not a promise of GPU compatibility).
- Splash that prepares the runtime on first launch; the extracted files
  are reused at subsequent launches.
- Android system Back **arrow or edge-swipe** opens an exit confirmation.
  Confirming closes the app process; **unsaved edits are lost**.
- No startup log toast and no automatically generated `blender-startup.log`
  file. Render output path remains configured.
- Separate package `hr.drnas.blendernativeprealpha2026` so the existing
  EMU app is not overwritten.

## Install / limitations

Download `Native-Blender-PreAlpha-0.1-arm64.apk` from the
[PreAlpha 0.1 prerelease](https://github.com/Frane12/DRNAS-Native-Blender/releases/tag/native-prealpha-v0.1)
once the CI checks/build finish successfully. Android ARM64 only.
Turn on APK installation from your trusted download source if needed.
This experimental build is CI/debug-signed; a later build might not update
over an older test APK if the signatures differ. **Export or back up your
.blend files before uninstalling an older installation.**

This is pre-alpha software. Not all GPUs, features, render paths, or
file-provider configurations are tested. No guarantee of stability. First
launch may need time to unpack runtime files; do not interrupt it unless
you deliberately exit. Blender rendering and asset handling can consume a
large amount of RAM and disk space.

## Source, licensing and attribution

Blender and source modifications are distributed under the applicable
upstream Blender GPL-2.0-or-later terms; preserve the upstream copyright
and license notices. Exact source revision: **simfeo/blender**
`d93bd33cba768e19ee4387a31c0ea137ee2f0047`.
The complete DRNAS modification scripts are published in
[`native-gui-upstream/`](https://github.com/Frane12/DRNAS-Native-Blender/tree/release/native-prealpha-0.1/native-gui-upstream)
at the release tag. See the included source-attribution file for details.
The CI workflow pins the exact source commit, runs the patches, builds the
ARM64 native lite APK and verifies its Android signature and library.

This is an experimental derivative of upstream Blender work, not an
official Blender Android release.
