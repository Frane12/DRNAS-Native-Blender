# Native Blender Pointer + IME v9 TEST (Android ARM64)

Small follow-up to working Controls v8, shipped as a **separate app** so v8 settings and installation stay untouched.

## User-reported fixes

1. **Relative cursor reaches the last pixels**: the full-screen trackpad now uses its measured size for cursor bounds; the custom 38dp cursor PopupWindow is no longer clipped away from the right/bottom edge. No change to native coordinate JNI or GPU rendering.
2. **Android keyboard numbers and letters**: the full-screen trackpad and control popups no longer use `INPUT_METHOD_NOT_NEEDED`, which can put touch-consuming windows *above* the soft keyboard. Popups are placed below the IME; the existing 1px `InputView` gets focus and an IME connection restart before the keyboard is shown on the next UI message.
3. **Android Gboard compatibility**: code-point Backspace/Delete and keyboard Enter/Done action now forward through Blender's existing native key JNI. Normal letter/number/Unicode composition still uses upstream `nativeOnCommitText()`, not synthetic button shortcuts.

Only Java patching/DEX/APK repack. The confirmed v7 native `libblender.so`, Vulkan driver libraries and all other native binaries remain byte-identical. No expensive native compilation.

**Validation needed on device:** enable Relative Mouse and move to all four screen corners. Open a Blender text or number field with LMB; tap the Android keyboard control and type digits, letters and Backspace/Enter. Repeat with Relative Mouse switched off. Test both landscape orientations and with Gboard visible. Build/compile success does not prove the Gboard and cursor behavior on the device.
