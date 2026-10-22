# DRNAS Native Blender Full LAB 1

Separate experimental app based on Alpha 1.0 commit 5dad4dec8dd224523f8618ab7bb1e4343c94c446.
Package: hr.drnas.blendernativefulllab. Version: 1.1-full-lab.1.

Retains Alpha controls, English/Croatian overlay, default Stretch, GPU picker,
and the ten pinned GPU drivers. Uses a new orange/blue LAB launcher icon.

Build target: pinned simfeo/blender d93bd33cba768e19ee4387a31c0ea137ee2f0047,
Android FULL configuration: Cycles CPU, FFmpeg, USD, OpenVDB, Alembic,
MaterialX and the other upstream full features. OIDN is explicitly disabled
until its separate static Android dependency is integrated. Cycles GPU and
new Wacom/stylus integration are not included in LAB 1.

The workflow compiles new native code, restores matching compiler/dependency
caches, saves compiler progress even on failure and uploads CMake diagnostics.
No public release is created automatically. Build success is not device validation.

First device checks: startup, GPU selection, open a COPY of a small blend,
edit/save/reopen, Cycles CPU render of a small scene, textured Eevee preview,
then import/export and video. Record errors before increasing scene size.

Icon: generated with the built-in image generator. Prompt: square Android
launcher icon, Blender-inspired orange metallic swirl, cyan center, charcoal
background, violet LAB badge, bold readable silhouette and safe margins.
