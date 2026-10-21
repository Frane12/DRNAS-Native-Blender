# DRNAS Native Blender — Android ARM64

**An unofficial, open-source Android experiment bringing Blender to ARM64 phones with a native Android runtime and DRNAS touch controls.**

[Native Blender PreAlpha 0.1 — release page](https://github.com/Frane12/DRNAS-Native-Blender/releases/tag/native-prealpha-v0.1) · [Build and verification](https://github.com/Frane12/DRNAS-Native-Blender/actions/workflows/native-gui-controls-build.yml) · [DRNAS EMU Blender v1.1](https://github.com/Frane12/Testturnip/releases/tag/blender-v1.1)

> **PRE-ALPHA / TESTING ONLY.** The native APK is published **only if** the ARM64 build, signature checks and packaging checks pass. A successful CI build is **not** proof that every feature works on a real phone. This is not an official Blender Foundation release.

## Why two DRNAS Blender projects?

There are **two independent ways** to explore Blender on Android. They are complementary research tracks, not claims that one is universally faster or better.

| | **DRNAS Native Blender — PreAlpha 0.1** | **DRNAS EMU — Blender v1.1 Preview** |
| --- | --- | --- |
| Approach | Blender **Android ARM64 native** application (lite build) | **Windows ARM64** Blender in a DRNAS **Wine/X11/Vulkan** Android compatibility environment |
| Windows / Wine layer | **Not required** | **Required**; this is a compatibility-layer approach, not necessarily x86 emulation |
| Blender base | [simfeo/blender Android fork](https://github.com/simfeo/blender) at pinned commit d93bd33cba768e19ee4387a31c0ea137ee2f0047, with DRNAS native patches | **Blender 4.5.14 LTS (Windows ARM64)** in the published EMU preview |
| User interface | Native Android GHOST/JNI integration and DRNAS touch overlay | DRNAS-managed Wine/X11 display, touch mouse controls and keyboard |
| GPU path | Experimental **native Vulkan** viewport integration; Adreno 810 tuning exists in source | Vulkan through the DRNAS compatibility stack; GPU-dependent driver/fallback routing |
| Features | **Lite / incomplete**; do not expect desktop feature parity | Runs the Windows desktop app, but install, secondary windows and rendering may be limited by integration |
| Current evidence | CI source checks and native APK build track; **device compatibility and render output require testing** | Existing public preview; **basic viewport editing and zoom exercised on Adreno 840** |
| Installation | Separate Android ARM64 APK; may require runtime extraction on first launch | Separate EMU Android APK and Windows-application environment setup |
| Best for testing | Native startup, direct Vulkan viewport, touch integration, responsiveness | Desktop-workflow compatibility, file loading and a mature Blender interface on Android |

**Important:** Both projects run on ARM64 hardware, but their **software stacks are different**. Native does not automatically mean faster; compare equivalent scenes on the same device before claiming a performance gain. The two APKs are separate and should not overwrite one another.

## What PreAlpha 0.1 includes

- Native Blender **lite** Android build, native ARM64 library and experimental Vulkan viewport.
- DRNAS touch overlay: **LMB/RMB, zoom, keyboard shortcuts and adjustable controls**.
- UI scaling and an experimental **Adreno 810** profile (not a compatibility guarantee).
- First-run splash and runtime extraction; later starts may reuse extracted data.
- Android system **Back / edge swipe** with exit confirmation. **Save before exiting**.
- No automatically displayed startup-log popup or default startup-log file; this is **not** a claim that diagnostic tools or crash reports are unavailable.
- An **isolated Android package** so the existing DRNAS EMU app is not replaced.

## Download and first test

1. Use the [PreAlpha 0.1 release page](https://github.com/Frane12/DRNAS-Native-Blender/releases/tag/native-prealpha-v0.1) **after** GitHub Actions publishes a verified APK.
2. Download **Native-Blender-PreAlpha-0.1-arm64.apk** and check **SHA256SUMS.txt**.
3. On an Android ARM64 device, install the APK, open it and allow the first-start initialization to finish.
4. Start with the default cube. Test orbit/rotation, zoom, selection, LMB/RMB and keyboard shortcuts.
5. Try opening and saving a **copy** of a small .blend file; do not test with your only copy.
6. Report the **device model, Android version, GPU, APK version, steps to reproduce and observed result** in [GitHub Issues](https://github.com/Frane12/DRNAS-Native-Blender/issues).

**Known limitations:** pre-alpha crashes and missing features are expected; GPU/Vulkan support, file providers, viewport correctness, rendering, add-ons, memory use and large scenes have not been comprehensively validated. The lite build is **not** a full desktop replacement. A CI/debug signing key can change between test APKs; **back up projects before uninstalling** an earlier build if a direct update fails. Unsaved edits are lost when exiting.

Read the [full PreAlpha 0.1 release notes](https://github.com/Frane12/DRNAS-Native-Blender/blob/release/native-prealpha-0.1/native-gui-upstream/RELEASE_NOTES_PREALPHA_0_1.md).

## Roadmap — next steps (goals, not delivered features)

1. **Validate first-frame reliability:** collect reproducible cold/warm-start, scene-loading, touch-input and crash reports from real devices.
2. **Stabilize native Vulkan:** verify Adreno 810/840, then expand to supported Mali and Xclipse devices only when evidence is available; investigate visual artifacts, memory pressure and render paths.
3. **Finish daily editing workflows:** file opening/saving, Android storage integration, keyboard, touch customization, safe return from secondary/render windows and lifecycle handling.
4. **Measure native versus EMU:** same phone, GPU, Blender scene and viewport settings; compare launch time, frame time/FPS, RAM, battery/thermals and functional correctness.
5. **Harden distribution:** reproducible pinned builds, checksums, source attribution, faster incremental CI builds, clearer compatibility matrix and tester feedback.

## Source, transparency and attribution

- **Native source base:** [simfeo/blender](https://github.com/simfeo/blender/tree/d93bd33cba768e19ee4387a31c0ea137ee2f0047) at pinned commit **d93bd33cba768e19ee4387a31c0ea137ee2f0047**.
- **DRNAS modifications / release branch:** [native-gui-upstream](https://github.com/Frane12/DRNAS-Native-Blender/tree/release/native-prealpha-0.1/native-gui-upstream) and [release workflow](https://github.com/Frane12/DRNAS-Native-Blender/blob/release/native-prealpha-0.1/.github/workflows/native-gui-controls-build.yml).
- **Separate DRNAS EMU preview:** [Testturnip / Blender v1.1](https://github.com/Frane12/Testturnip/releases/tag/blender-v1.1). The EMU project is **not** included in this repository; no private EMU source was imported.
- **Licensing:** Blender and derived modifications remain subject to applicable GPL and upstream notices; third-party components keep their respective licenses. This project is not affiliated with or endorsed by the Blender Foundation.

**Our goal: useful desktop-class creative tools on Android through careful, measurable open-source experimentation — one testable milestone at a time.**
