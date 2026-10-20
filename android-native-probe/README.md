# DRNAS Android native Vulkan / GUI LAB

Experimental branch `feature/native-android-vulkan-gui`. Built to run alongside
the original `DRNAS Native LAB` and EmuDRNAS (different application ID).

## What this actually does

1. Starts a Java `SurfaceView` backed by a real Android `ANativeWindow`.
2. Creates a Vulkan instance with `VK_KHR_android_surface` and a presentation
   queue on the device's actual Vulkan driver (Adreno, Mali, Xclipse, etc.).
3. Creates a Vulkan swapchain, records a real render pass, clears a frame
   dark teal and presents it to the phone. Result includes the GPU name and
   supported Vulkan API version or a specific error.
4. Displays **experimental DRNAS controls**: LMB and RMB touch press/release
   buttons, relative zoom slider, movable buttons/zoom (EDIT mode), immersive
   fullscreen toggle and COPY log. Native input events are captured as a
   test ABI for the future GHOST adapter.
5. Checks the separately packaged headless Android ARM64 Blender ELF with
   `--version` through the LTS button.

**THIS IS NOT YET BLENDER'S VIEWPORT.** The pictured Vulkan frame is the
small native Vulkan proof of rendering. The Blender ELF built in the headless
workflow has `WITH_VULKAN_BACKEND=OFF`. It cannot magically accept this
window via `--gpu-backend vulkan`. We must develop an Android-specific GHOST
window/event backend and rebuild Blender with Vulkan before a genuine
graphical Blender interface can be displayed.

## Next engineering steps

- Validate `VkResult`, driver version and surface presentation on Adreno,
  Mali and Xclipse phones (including app suspend/resume).
- Wire Android touch, button/key/wheel events into an Android GHOST bridge,
  testing event order, surface recreation and input focus.
- Enable Blender Vulkan backend, adapt GHOST Android window/system and
  Vulkan `VkSurfaceKHR` handoff; patch Bionic/platform paths as needed.
- Draw Blender UI via GPU backend (not Android-native UI substitutes), then
  reuse DRNAS overlay ergonomics with customizable controls.
- Keep existing EmuDRNAS and proven headless ELF builds untouched until
  graphical port passes real device tests.

## Build

`.github/workflows/native-vulkan-gui-lab.yml` creates a debug-signed APK and
checks Android ABI, package contents and checksum. It downloads the successful
native ELF from run 39487417634, verifies ELF64/AArch64/PIE/Android interpreter,
and strips debug symbols only from the APK copy. There is **no rerun of Blender's
~3200 native C/C++ compilation**. No release is published. The resulting APK
is specifically named **Vulkan GUI LAB**.
