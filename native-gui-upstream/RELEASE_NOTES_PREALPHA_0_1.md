# Native Blender PreAlpha 0.1 (Android ARM64)

**Public experimental pre-release — not an official Blender Foundation Android release.**

This is a **native ARM64 Blender lite** build based on
[simfeo/blender](https://github.com/simfeo/blender) at pinned source commit
`d93bd33cba768e19ee4387a31c0ea137ee2f0047`, compiled with DRNAS
Android GHOST/JNI controls and UI modifications.

### Highlights
- Real Blender GUI / native Vulkan viewport, without Windows emulation.
- DRNAS touch LMB/RMB, zoom, adjustable control sizes/positions and shortcut strip.
- Native keyboard shortcuts, per-device GUI scale and experimental Adreno 810 profile.
- Android **Back arrow / navigation gesture** now prompts to exit; confirming
  closes the application completely.
- Removed the startup log pop-up and disabled writing `blender-startup.log`.
  Render output directory selection stays enabled.
- Animated Blender initialization screen and isolated Android package.

### Please read before installing
- **PRE-ALPHA**: crashes, missing features, incompatible GPUs and rendering
  failures are possible. Testing so far is not a compatibility certification.
- Requires Android **ARM64** with suitable Vulkan support; not for x86 devices.
- **Unsaved edits are lost** if you confirm Exit; save your .blend first.
- First launch extracts runtime assets and can take some time.
- The test APK uses a CI/debug signature. If Android rejects an update over a
  previous test APK, back up your files and uninstall the older installation first.
- Blender source and DRNAS patches: [corresponding release source](https://github.com/Frane12/DRNAS-Native-Blender/tree/release/native-prealpha-0.1/native-gui-upstream)
  + upstream exact [Blender source commit](https://github.com/simfeo/blender/tree/d93bd33cba768e19ee4387a31c0ea137ee2f0047).
  Blender and associated modifications remain subject to the applicable GPL terms.

**Files:** `Native-Blender-PreAlpha-0.1-arm64.apk`, `SHA256SUMS.txt`,
`SOURCE-ATTRIBUTION.txt`.
