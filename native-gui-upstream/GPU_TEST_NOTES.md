# Native Blender GPU v7 TEST

Based on user-accepted v6 controls. Separate package `hr.drnas.blendernativegputest2026v7`; no public release replacement.

- System Vulkan is the default. Driver choices are filtered by actual EGL renderer, not phone/SoC names.
- Exact seven Turnip and three PanVK packages from EmuExperimental `9de8de285352f4c3f771343b3241bb2d1d4d9ef3`, checksum-pinned in `gpu_drivers.json`.
- A6xx/A7xx: Mesa Turnip R6. A810: S Ultimate and H2.7. A830: S1 Smart and H2.4. A840: H2.9 and H2.8.
- Mali G52/G72/G76: PanVK R4/R3; G52 additionally V7. Other Mali and Xclipse retain system Vulkan. Hardware eligibility is not proof of working Blender rendering.
- Custom drivers retain Android's Vulkan loader/WSI through libadrenotools, pinned `8fae8ce254dfc1344527e05301e43f37dea2df80`. Drivers reside in Android-extracted nativeLibraryDir. Experimental, untested on physical devices in CI.
- If a custom driver never presents a first frame, the next app launch resets selection to system. A native crash after first frame is not automatically classified as a startup failure.
- Resolution picker: Automatic, Native, 960x544, 1280x720, 1600x900, 1920x1080, 2560x1440. Presets are upper bounds preserving the physical screen aspect, with actual dimensions displayed. No upscale. Even-pixel rounding maps X/Y input independently.
- Driver/resolution changes take effect at the next process start. Save work before closing. No forced restart from settings.
- No Wine, DXVK or VKD3D in the native path. Emu-specific OpenGL/Zink fallbacks are not native Blender backends and are not presented as working native options.
- All v6 controls, independent sizes, tactile/latching keys, spring zoom, cursor options and save-before-exit remain.
- Compiler cache is restored and saved even on compilation failure; drivers are reused, not rebuilt. The first native integration needs a Blender build.

Test on A840: system vs H2.8/H2.9 at identical resolution and scene. Check Workbench, Material Preview, EEVEE rendered mode, color picker, render return, suspend/resume and save/exit. Repeat on actual A6/A7, A810/A830 and supported Mali models before claiming compatibility.
