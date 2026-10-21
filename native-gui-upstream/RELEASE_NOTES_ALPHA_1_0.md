# DRNAS Native Blender — Alpha 1.0 (Android ARM64)

**Alpha 1.0 is a public test release, not a PreAlpha and not yet a stable production release.**

Native Blender UI and Vulkan viewport on ARM64 Android, with a custom DRNAS floating touch/keyboard overlay. This release builds on the working v10 controls, incorporates the native Android keyboard and relative-pointer fixes, and adds a first-run full-display default.

## Install / start

1. Download **DRNAS-Native-Blender-Alpha-1.0-arm64.apk** from Assets below (NOT a Source code ZIP).
2. Install it on an ARM64 Android device that supports Vulkan; allow app installation through your browser or Files app when Android prompts.
3. On first start, wait for Blender's setup to finish. If prompted, grant **All files access** so Blender can open or save projects outside its private folder.
4. **Stretch screen is enabled automatically on the first launch.** You may disable it later: your saved preference will be respected.
5. The DRNAS overlay is **English by default**. Blender's own menus are controlled separately by Blender Preferences.

> This Alpha is packaged as a separate app from the earlier v10 test and PreAlpha. Different app identifiers (and CI signing keys) mean existing project paths/preferences do not automatically transfer; back up your .blend files first.

## Where is the controls menu?

Tap **⚙ Settings** on the floating shortcut/keyboard bar. The options panel can scroll: drag inside it to reach lower sections and press **Close settings ✕** to return to the viewport.

**Menu reference**

| Menu item | What it does |
| --- | --- |
| **DRNAS LANGUAGE** | Choose **English** or **Hrvatski** for the DRNAS controls. Restart the app to apply all overlay labels. English is the default on first install. This does *not* translate upstream Blender's own built-in menus. |
| **GPU DRIVER** | Pick a compatible bundled GPU driver or **System Vulkan (default)**. Hardware determines what appears. Save your work and restart to apply driver changes. Selecting a driver is not proof of successful GPU initialization. |
| **RESOLUTION** | Choose **Automatic**, **Native**, or an aspect-correct reduced render-size preset. Restart to apply the chosen rendering preset. |
| **Stretch screen** | ON by default on the first start. Uses the full available Android window; can be toggled OFF and back ON. Lower render resolutions scale to the available window while maintaining their aspect ratio. |
| **BUTTON SIZE / KEYBOARD SIZE** | Adjust the DRNAS shortcut buttons independently of the floating mouse/zoom window. |
| **MOUSE AND ZOOM SIZE** | Resize the LMB/RMB + zoom dock. |
| **Relative mouse / touchpad** | ON uses swipe-to-move mouse; OFF uses direct touchscreen input. Use the mouse-speed setting for sensitivity. |
| **Pointer click indicator / Cursor size** | Configure the on-screen mouse cursor and click effect. |
| **Smooth zoom / Gesture sensitivity** | Configure zoom, pan and gesture response. |
| **BLENDER UI SCALE** | Adjust Blender UI density (not Android screen resolution). Restart Blender after changing it. |

## Floating mini windows and controls

- **⠿ handle:** drag the mouse/zoom dock or the shortcut/keyboard dock anywhere. Positions are saved.
- **▾ / ▣ mouse window:** minimize to a small grip and restore, useful in Blender's Open/Save dialog.
- **LMB / RMB:** tap, hold or double-tap to latch where the control supports it; tap again to release a latched button. Controls are released safely when dialogs, editing and lifecycle changes require it.
- **ZOOM:** use the spring slider, release to stop. Its section can be hidden.
- **⌨ shortcut strip:** expand/collapse the shortcut keys (Move G, Rotate R, Scale S, Tab, axes, Undo, Save and others).
- **Gear above each group:** set group width, height and transparency. The keyboard editor also supports rows and button ordering.
- **Android soft keyboard:** focus a text or number field in Blender and open the keyboard button. Android IME sends letters, digits and editing keys through Blender's native input bridge. If typing seems stuck, close the keyboard and refocus the field.

**To exit:** use Android Back or the back/edge gesture; Blender offers save-before-exit confirmation. Do not force-close the app before a save confirms success.

## What changed from the v10 test

- First-run **Stretch screen = ON** (stored only if no prior preference exists; choosing OFF remains persistent).
- **Alpha 1.0** app/version naming.
- DRNAS controls start in **English** with **English / Hrvatski** in Settings (a restart updates all overlay labels).
- Relative touchpad-to-viewport coordinates and floating compact windows inherited from v10, with v9 Android input/IME fixes.
- APK is repackaged using the **same verified native ARM64 Blender library and GPU driver binaries**; no native Blender recompilation is required for this UI-only release.

## Limitations, credits and support

This is **Alpha**, so device compatibility, IME focus, pointer positioning in some modal Blender dialogs, driver loading and render quality still require wider device testing. Do not use an Alpha as the only copy of important projects.

The Android native Blender foundation is based on the open-source Blender Android work by **simfeo/blender** (pinned Android GUI source), with DRNAS-specific Android overlay/packaging changes. Blender is free and open source under the GPL; upstream notices and bundled source/attribution information are retained in the repository.

Please report your Android version, GPU (Adreno/Mali/etc.), what failed, steps to reproduce, and a screenshot or log when practical. GitHub: https://github.com/Frane12/DRNAS-Native-Blender/issues
