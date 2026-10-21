# DRNAS Native Blender — Android ARM64

**Unofficial Blender Android native port experiments** maintained by DRNAS.
This repository contains source-level Android/GHOST modifications for an
upstream Blender fork and separate experimental build workflows.

## Public experimental PreAlpha 0.1

The [Native Blender PreAlpha 0.1 GitHub pre-release](https://github.com/Frane12/DRNAS-Native-Blender/releases/tag/native-prealpha-v0.1)
contains the ARM64 test APK **only after** its GitHub Actions build and
signature/integrity checks complete successfully.

- A real native Blender lite GUI, 3D Vulkan viewport and DRNAS Android input
  overlay; **no x86/Windows emulation**.
- System **Back arrow / edge-swipe** asks for exit confirmation and closes the
  app process when confirmed.
- No startup log popup or automatically written startup log file.
- Adjustable touch controls and native keyboard shortcuts.

**This is pre-alpha**, may not work across all Android GPUs, and is not an
official Blender Foundation release. Make a backup before uninstalling older
test builds. See [release notes and limitations](native-gui-upstream/RELEASE_NOTES_PREALPHA_0_1.md).

### Provenance & license

The GUI port uses [simfeo/blender](https://github.com/simfeo/blender)
at exact commit `d93bd33cba768e19ee4387a31c0ea137ee2f0047`
with the published DRNAS [patch scripts](native-gui-upstream/).
The experimental ARM64 lite native binary is built in CI from these sources.
Blender and modifications are distributed under their upstream GPL terms.

Earlier Android ELF/GHOST/Vulkan smoke-test work is retained in
[`android-native-probe/`](android-native-probe/).
