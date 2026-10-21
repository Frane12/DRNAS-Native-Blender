# Native Blender Floating Windows + Stretch v10 (Android ARM64 TEST)

User feedback: in Blender dialogs (especially the Open/File Browser), relative mouse and the control overlay can stop matching the stretched viewport; the toolbar obscures the dialog's lower fields.

## Changes
- **Relative pointer mapping:** the full-screen Android mouse popup and NativeActivity decor viewport can differ after stretch, rotation, immersive system bars and keyboard. Map the pointer's popup coordinates into the native decor viewport in *both* JNI GHOST cursor moves and visible pointer placement. Use decor's screen origin for its PopupWindow.
- **Two small draggable utility windows:** mouse/zoom dock and keyboard controls remain independent. Updated semi-opaque rounded window borders. Existing drag grips work in normal mode, no edit step.
- **Foldable mouse window:** new tiny minimize button collapses the LMB/RMB/zoom area to a compact grip + restore control. Existing shortcut keyboard strip has its own opener. Tap to restore. Saved across launches.
- **Stretch/rotation relayout:** on measured viewport resizing, reschedule overlay placement and relative cursor updates. Native rendering not modified.
- Preserve v9 Android IME fixes, existing input-hold semantics, per-group sizes, group editor, GPU selection, saved projects, and all native GHOST/Vulkan binary components byte-for-byte.

**Scope:** Java UI / DEX repack only, separate v10 package. Pixel-perfect mapping in Blender Open/Save dialogs and Gboard input still require a real-device acceptance test; no native binary rebuild was necessary.

**Test:** Open Blender's File Browser, drag the pointer to the left/right/top/bottom, click folder icons and Open/Cancel, then minimize and restore the mouse dock. Check Stretch on and off after relaunch and test Android keyboard input in a Blender text field. Keep v9 installed for comparison.
