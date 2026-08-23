# Snapdragon AI Studio 2.0 RC2B — Release Notes

**RC2B is the most stable, refined, and user-friendly Snapdragon AI Studio release candidate to date.** Building on RC2A, it delivers substantial improvements to Windows scaling, gallery workflows, image comparison, Phoenix Boost, plugin integration, and installer/output safety.

Validated on the Windows ARM64 development system and on RC2CleanTest, RC2B combines the strongest Phoenix UI, installer safeguards, and day-to-day workflow improvements delivered so far.

---

## 🌟 Highlights

* **Responsive Phoenix UI:** The affected Phoenix views have been responsively optimized for Windows scaling from 100% to 175%. Wrapping and local scroll areas keep content and critical actions accessible.
* **Synchronized Image Comparison:** Shared toolbar zoom controls combined with synchronized panning using normalized pan coordinates via mouse dragging.
* **Gallery Toolbar Adaptations:** The existing gallery toolbar has been rebuilt to be responsive, preserving search, sorting, thumbnail sizing, and filters while controlled wrapping was introduced at low widths.
* **Optional Hover Preview:** Persistent, toggleable quick-preview option on gallery thumbnail mouse hover (state saved across application restarts).
* **Text-Based Metadata Comparison:** Purely parameter-based metadata matching with clear status diagnostics (not a visual pixel comparison).
* **Robust Output Directories:** Clicking "Open Output Folder" opens the output folder configured for the current user and safely creates it if it does not yet exist.
* **Installer Safety:** Inno Setup excludes runtime outputs, and build_installer.py rejects the installer build if the frozen staging tree contains a runtime output folder.

---

## 🚀 Improvements Since RC2A

### Gallery
* Rebuilt the existing gallery toolbar to be responsive. Searching, sorting, thumbnail sizing, and filtering are preserved. The hover on/off switch was added, and toolbar groups wrap in a controlled manner at low widths.
* The "Open Output Folder" action opens the output folder configured for the current user and safely creates it if it does not yet exist.
* Introduced a toggleable **Hover Preview** switch next to the output folder button. When enabled, hovering over image thumbnails displays a quick preview. When disabled, hover previews are blocked, and any active preview window is closed immediately. Selection, double-click, and context menu actions remain independent of the hover state.

### Image Comparison
* Integrated a shared zoom toolbar containing *Fit*, *50%*, *100%*, and *200%* controls for the comparative view.
* Enabled mouse-panning on zoomed-in images (panning is done by holding down the left mouse button).
* Implemented the **Synchronous** toggle:
  * **Synchronous: On:** Transfers normalized pan positions between the two image views.
  * **Synchronous: Off:** Allows independent pan positioning.
* Added a text-based comparison for embedded generation metadata (prompt, seed, steps, etc.). Status messages distinguish between missing, one-sided, identical, or differing parameters. No visual pixel differences or color highlights are applied.

### Model Management and Generation UI
* Restructured model inspectors to support scrollbars so that the bottom installation action bars remain visible and accessible across various window sizes.
* Refined layout margins and alignment for Dark and Light themes under high DPI scaling.

### Phoenix Boost
* Refined the **Boost Preview** layout into a compact, space-saving layout.
* Positions original and optimized prompts (as well as negative prompts) side-by-side.
* Embedded control actions are fixed and accessible outside the scroll area at the bottom.
* Made the preview window maximizable and restorable for inspecting long texts, with scrollbars serving as fallback.

### Plugins
* The plugin installation area uses existing Phoenix components and PHOENIX_THEME-based styling.

### Installer and Output Safety
* Re-architected Inno Setup rules to structurally exclude runtime-output directories from the packaged installer.
* Rejects the installer build via build_installer.py if the frozen staging tree contains a runtime output folder.

### Documentation and Languages
* Updated English, German, and Spanish user guides to represent the current RC2B features.

---

## 📥 Installation / Upgrade

For normal use, download the pre-packaged installer:
1. Obtain `SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe`.
2. Execute the setup program on Windows 11 ARM64 and complete the wizard.
3. Launch the application from the Start menu.

*Note: Existing model directories will be automatically detected and verified by the Phoenix Engine.*

---

## 🔍 Validation

Validation was performed on Holger's Windows ARM64 development machine:
* **Testing Scope:** Focused direct Python-based tests and direct frozen-app validations.
* **Clean Install Test:** `RC2CleanTest` was executed to verify that the corrected installer was cleanly installed.
* **Upgrade / Over-installation Test:** Afterwards, the final RC2B installer was validated as an over-installation.
* **Binary Verification:** Confirmed that the installed executable matched the final frozen SHA-256 hash.
* **Layout & Feature Verification:** Tested under 175% screen scaling in both Light and Dark themes, verifying dynamic wrapping and scroll fallback in narrow and maximized windows, empty gallery at startup, hover persistence, plugin design, and automatic creation/opening of the output directory.
* *Note: Validation does not cover a complete automated test suite.*

---

## ⚠️ Known Limitations

* **Release Candidate Status:** This version is for pre-production validation and testing.
* **Target Hardware:** Windows 11 ARM64 running on Qualcomm Snapdragon X Plus or Snapdragon X Elite processors.
* **Internet Connection:** Required for initial model, component, and framework setup (e.g., QAI AppBuilder, Ollama, Qwen).
* **Feature Scope:** Specific inference backends and prompting functions are dependent on active model capabilities.
* **Metadata Abstraction:** Metadata comparison is purely text-based and does not compare image pixels or highlight differences visually.

---

## 📦 Artifacts

### Windows ARM64 Installer
* **Filename:** `SnapdragonAIStudio-2.0.0-rc.2b-ARM64-Setup.exe`
* **File Size:** `272026975` Bytes
* **SHA-256:** `59BE27EDF318990987E80ED3EFC7C896E8D651A456AE45BE2C8F15C02C01BDA3`

### Frozen Application Executable
* **SHA-256:** `D8CF83FFA8AED8D9241B29998EE6814E2F6F63118D2080919BA2E5D99B52E12C`
