# Native Blender PreAlpha 0.1 — Android ARM64

> **PUBLIC PRE-ALPHA · EXPERIMENTAL · TESTING ONLY**
>
> Unofficial Android ARM64 Blender **lite** port with DRNAS native touch controls. **Not an official Blender Foundation release.** The APK becomes available only after GitHub Actions successfully builds it and verifies its Android signature, packaged native library and runtime assets. **A passing build does not imply validated on-device rendering or compatibility.**

## What's in this pre-alpha?

- Android-native **ARM64** Blender lite application and experimental **Vulkan** 3D viewport path — **no Windows / Wine compatibility layer**.
- DRNAS native input controls: floating **LMB/RMB**, zoom, shortcut strip, keyboard inputs and adjustable touch button sizing and placement.
- Android-oriented UI scaling, runtime initialization splash and experimental **Adreno 810** profile.
- **Back button / edge-swipe exit confirmation**. Confirming exit closes the application; **save first**.
- Cleaner start: no automatic startup-log popup and no default **blender-startup.log** creation.
- A **separate app identity**, so it can coexist with DRNAS EMU.

## Native Blender vs. DRNAS EMU

DRNAS already has a **separate public Blender v1.1 preview** using **Blender 4.5.14 LTS for Windows ARM64** through a DRNAS **Wine/X11/Vulkan** compatibility environment. This **native** pre-alpha experiments with a shorter Android-specific stack, while the EMU preview explores running the fuller Windows desktop workflow.

| | Native PreAlpha 0.1 | DRNAS EMU Blender v1.1 |
| --- | --- | --- |
| Executable | Android **ARM64** native lite Blender | **Windows ARM64** desktop Blender |
| Runtime | Android GHOST/JNI and native Vulkan path | Android + DRNAS Wine/X11/Vulkan compatibility stack |
| Windows layer | **No** | **Yes** (Windows ARM64 does not imply x86 emulation) |
| UI | Native Android DRNAS touch overlay | DRNAS Wine/X11 mouse, touch keyboard and display integration |
| Evidence | Automated source/build/signature checks; broad real-device testing **pending** | Existing public device preview; basic editing and zoom exercised on Adreno 840 |
| Trade-off | Fewer compatibility layers, but lite feature set and immature integrations | More desktop features, but additional install/runtime/graphics complexity |

**No FPS, GPU-support or stability advantage is claimed yet.** We will compare both approaches with identical scenes on the same hardware.

**[DRNAS EMU Blender v1.1 public preview](https://github.com/Frane12/Testturnip/releases/tag/blender-v1.1)** · **[Native project README](https://github.com/Frane12/DRNAS-Native-Blender/tree/release/native-prealpha-0.1)**

## Installation and first-run test

1. Download **Native-Blender-PreAlpha-0.1-arm64.apk** and the included **SHA256SUMS.txt** from this release once published.
2. Install it on an **Android ARM64** phone with suitable Vulkan support. It is separate from EMU.
3. The first launch may unpack runtime files. Do not mistake this setup for a hang without checking whether it progresses.
4. With a **copy** of a .blend project, test opening/saving, viewport rotation, selection, zoom, LMB/RMB and Android Back handling.
5. Report reproducible issues with **device / Android version / GPU / build / reproduction steps / screenshots or optional logs** at [GitHub Issues](https://github.com/Frane12/DRNAS-Native-Blender/issues).

**Read before use:** crashes, incomplete features, missing add-ons, incorrect rendering, Vulkan driver problems, unresponsive secondary windows, high memory use and device-specific incompatibilities are possible. This is **not feature-equivalent to desktop Blender**, and **rendering has not been certified**. Back up projects before testing. Unsaved edits will be lost if you confirm Exit. The APK is CI/debug signed; updates may fail if the signing certificate changes. Back up files before removing older test installs.

## Next milestones

1. **PreAlpha 0.1 feedback:** real hardware first frame, cold/warm launch, cube manipulation, files, crashes and control ergonomics.
2. **Native GPU testing:** Vulkan correctness, Adreno profiles and carefully scoped testing on other supported GPU families; prioritize reproducible results over unsupported acceleration claims.
3. **Editing workflow polish:** file picker/storage, touch customization, responsive secondary windows, render-window exit and lifecycle recovery.
4. **Benchmarked comparison:** native vs. DRNAS EMU on the **same device + same .blend scene**, measuring FPS/frametime, startup, RAM, thermal load and feature parity.
5. **PreAlpha 0.2+ only after evidence:** fix highest-impact failures, improve incremental build caching and maintain device/test matrix and changelog.

## Files and reproducibility

- **Native-Blender-PreAlpha-0.1-arm64.apk** — experimental arm64 Android application
- **SHA256SUMS.txt** — downloaded asset checksum
- **SOURCE-ATTRIBUTION.txt** — source and licensing attribution

**Upstream Android source:** [simfeo/blender](https://github.com/simfeo/blender/tree/d93bd33cba768e19ee4387a31c0ea137ee2f0047) pinned to **d93bd33cba768e19ee4387a31c0ea137ee2f0047**. **DRNAS native modifications:** [public patch scripts](https://github.com/Frane12/DRNAS-Native-Blender/tree/release/native-prealpha-0.1/native-gui-upstream). [Build workflow](https://github.com/Frane12/DRNAS-Native-Blender/blob/release/native-prealpha-0.1/.github/workflows/native-gui-controls-build.yml) documents APK compilation and verification. Blender is subject to applicable upstream **GPL** terms; retain the original licenses and copyright notices.

**Independent community effort by DRNAS · experimental research release · no upstream endorsement.**
