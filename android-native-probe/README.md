# DRNAS Native ARM64 LAB (isolated)

This app is **not** the graphical Blender application. It is a separate Android
smoke-test APK that can be installed on a phone without a PC or Termux.

- The first test runs an actual NDK-built ARM64 PIE executable directly from
  Android's app-owned `nativeLibraryDir` (it must be installed as `lib*.so`).
- If a real Android ARM64 Blender executable is included, the second test runs
  `blender --version` with a 20-second timeout and shows stdout / errors.
- Use the **Copy log** button to share text. It has no network permission.
- It is a *debug-signed*, separately named LAB app; it does not overwrite
  DRNAS Emu or the production Blender APK.
- Do not package Linux x86_64 Blender binaries. An Android ELF must be
  AArch64, linked for Android/Bionic and be PIE (ET_DYN).

## CI

`.github/workflows/native-apk-smoke.yml` builds a basic test APK on its
branch. An optional `blender_run_id` workflow dispatch input can attach an
existing successful `DRNAS Native Blender ARM64 feasibility` artifact
from the same repository. This is rejected if the ELF is not a PIE AArch64
Android executable. A working binary/GUI is **not** implied by a successful
APK compile.

## Known limitations

The existing Blender compilation workflow is headless (Vulkan disabled);
the APK only tests native program launch, not Blender UI. A completed
headless ELF still requires device-level dependency and runtime validation.
