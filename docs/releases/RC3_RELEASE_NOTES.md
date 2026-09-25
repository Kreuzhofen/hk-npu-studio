# HK NPU STUDIO – VERSION 2.0 RC3

## Highlights

- Phoenix Image Lab now opens AI Photo Restoration directly.
- Faithful Restore keeps results anchored to the source image.
- 4× upscaling preserves the native source workflow.
- Source detail preservation remains part of the restoration path.
- Dust Cleanup V4 removes conservatively detected dust, specks, and small defects.
- Neural restoration runs locally through QNN/HTP on the Snapdragon® NPU.
- The required FiDeSR Strong Photo Restore models are bundled with the installer; no separate restore-model download is required.

## Improvements

- Native multi-tile restoration processes large images without a global source downscale.
- Memory handling and runtime performance were improved while preserving the restoration path.
- German, English, and Spanish release texts describe the same feature set.
- The release UI was simplified so Phoenix Image Lab leads directly to AI Photo Restoration.
- Grayscale input remains grayscale in the RC3 product path.
- Installed application and user-data paths containing spaces are supported by the Photo Restore QNN input path.
- Drag and drop is optional at startup. If TkDND cannot load on Windows ARM64, the application continues with the standard file dialog.
- Large precompiled Photo Restore contexts are stored without redundant LZMA2 recompression to reduce installer build and installation time; normal application files remain compressed.

## Fixed

- Issue #1: removed hardcoded product paths and improved portability.
- Issue #2: aligned declared runtime dependencies with the release requirements.
- Issue #3: added Snapdragon X2 Elite hardware detection.
- Issue #4: added Python resolver and Python identification compatibility in the code. The issue tracker status is not asserted here.

## Not included in RC3

- Colorization and DDColor as visible product functions
- Generative Fill
- Retouch
- Object Removal
- Artificial microtexture generation
- Skin reinjection

The related backend research or implementation files may remain in the repository, but these functions are not exposed in the RC3 release interface.

## QA

- Final release QA: PASS
- 164 focused release QA tests passed with 0 failures
- Small real restoration completed in 27.42 seconds
- Large real restoration completed in 415.14 seconds
- Navigation/UI follow-up: 49/49 passed
- Locale follow-up: 55/55 focused tests passed
- Version follow-up: 22/22 passed
- `py_compile`: PASS
- `git diff --check`: PASS
- Real small and large restoration runs completed without tile seams, black frames, or out-of-memory failures
- Neural restoration inference uses QNN/HTP only, with no CPU- or GPU-AI fallback
