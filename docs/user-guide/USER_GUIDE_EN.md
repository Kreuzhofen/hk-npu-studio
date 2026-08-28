# HK NPU STUDIO – Phoenix Engine
## User Guide – Version 2.0 RC2B

> **Independent open-source project for Windows on Snapdragon.**  
> HK NPU STUDIO is not an official product of Qualcomm Technologies, Inc. and is not sponsored or supported by Qualcomm.

---

## 1. Welcome

HK NPU STUDIO is a desktop application for local AI image generation on Windows 11 ARM64 PCs with Snapdragon processors. The **Phoenix Engine** manages model handling, preparation, and execution of the supported AI pipelines.

RC2B puts particular emphasis on a guided workflow: **Install → select a model → generate an image.** Technical details should remain in the background as much as possible during normal use.

Image generation itself runs locally on the PC. Once a required model has been set up, the actual generation process generally does not require a cloud image-generation service.

---

## 2. System Requirements

### Supported Platform

- Windows 11 ARM64
- Qualcomm Snapdragon X Plus or Snapdragon X Elite as the primary target platform
- Current Windows and Qualcomm drivers recommended
- Sufficient free SSD space for the models you want to use

### Memory and Storage

Actual requirements depend on the model. Larger models require significantly more storage than the application itself. Stable Diffusion 3.5 Medium downloads several gigabytes during setup; the Qualcomm model download is currently approximately **3.24 GB**, with additional installation and working files created during setup.

### Internet Connection

An internet connection is required when necessary components or models are downloaded for the first time. After successful installation, supported image generation runs locally.

---

## 3. Installing RC2B

1. Download the current ARM64 installer from the official HK NPU STUDIO GitHub release.
2. Start `HKNPUStudio-2.0.0-rc.2b-ARM64-Setup.exe`.
3. Follow the Windows setup wizard.
4. Start **HK NPU STUDIO** from the Start menu or the created shortcut.

> **Windows SmartScreen:** Windows may display a warning for a release that is not widely recognized or commercially signed. Only use installers obtained from the official project repository.

A separate Python installation is not required for normal use of the published installer.

---

## 4. First Start

RC2B guides new users through initial setup much more clearly than earlier release candidates.

The home page shows the current setup state. If no usable model has been configured yet, the application guides you to the Model Manager. After successful setup, the readiness status is updated and you can proceed directly to your first image generation.

### Basic Workflow

1. Start HK NPU STUDIO.
2. Open the Model Manager.
3. Select the desired supported model.
4. Start the offered installation workflow.
5. Allow installation and validation to complete.
6. Activate the model or wait for automatic activation.
7. Switch to image generation.

For the normal guided workflow, you do not need to select individual internal ONNX, QNN, or model components.

---

## 5. Model Manager

The Model Manager displays the models known to HK NPU STUDIO and their current state.

Depending on the model and development status, a model may be marked as installed, not installed, available, or experimental.

### Installed

The required model package was found and successfully validated.

### Active

The model is currently selected for image generation.

### Not Installed

The required model files have not yet been fully set up.

### Experimental / In Development

These models are not part of the same stable user workflow as released models. Experimental entries may have additional requirements or may not yet be intended for everyday use.

> **Recommendation:** For your first steps, use a model explicitly shown as available and supported in the Model Manager.

---

## 6. Installing Models

RC2B uses different sources and installation methods depending on the model. The Model Manager attempts to hide these differences and provide a guided workflow.

### Stable Diffusion 1.5

Stable Diffusion 1.5 is a compact entry point for local image generation and is particularly suitable for fast 512×512 workflows. With a supported NPU variant, Phoenix handles the required package validation and activation.

### Stable Diffusion 2.1

Stable Diffusion 2.1 is also available as a Snapdragon/Qualcomm-oriented image-generation path. Installation and activation are handled through the Model Manager according to the source configured for the model.

### Stable Diffusion 3.5 Medium

RC2B includes a substantially more automated setup path for **Stable Diffusion 3.5 Medium via Qualcomm QAI AppBuilder**. This workflow is described separately in the next section.

---

## 7. Setting Up Stable Diffusion 3.5 Medium

SD3.5 setup is more extensive than smaller model packages. Phoenix therefore automates as many steps as possible.

### What Phoenix Handles Automatically

The guided workflow can:

1. locate the required Qualcomm QAI AppBuilder ZIP,
2. prepare and extract the archive,
3. prepare required Python components for setup,
4. run the Qualcomm SD3.5 script,
5. download the required model files,
6. import the generated files into HK NPU STUDIO,
7. create the manifest and validation information,
8. validate the installation,
9. activate the model afterwards.

The installation window displays the current step and progress throughout the process.

### Qualcomm QAI AppBuilder

This setup path uses Qualcomm's official QAI AppBuilder project. Phoenix searches for the expected ZIP archive in the Downloads folder. If it cannot be found automatically, the application can ask you to select the ZIP archive.

The ZIP file itself is not deleted as a user file by the normal installation process.

### Model Download

During setup, the Qualcomm script downloads the required SD3.5 files. The download is currently approximately **3.24 GB**. Speed and duration depend on the internet connection, storage device, and system state.

Do not close HK NPU STUDIO during this process; allow the installation to complete.

### Completion

After setup, the model files are validated and the model becomes available to HK NPU STUDIO. The successful RC2B user workflow was tested as a complete chain:

**not installed → setup succeeds on the first attempt → Qualcomm download → import/validation → activation → real image generation.**

---

## 8. Generating an Image

After selecting an installed model, switch to image generation.

1. Enter a description of the desired image in the **Prompt** field.
2. Optionally enter a **Negative Prompt**.
3. Review the desired generation parameters.
4. Click **Generate**.
5. Wait for the Phoenix Engine to complete the pipeline.
6. The finished image is displayed and added to the appropriate history/output area.

The required time depends heavily on the model, resolution, settings, and backend in use.

---

## 9. Prompt and Negative Prompt

### Prompt

The prompt describes **what should appear in the image**.

Example:

> Portrait of an astronaut, cinematic lighting, fine details, realistic style

Specific information about subject, environment, lighting, perspective, and style helps the model interpret your request.

### Negative Prompt

The Negative Prompt describes unwanted properties. Its effect depends on the model and pipeline.

Example:

> blurry, bad anatomy, text, watermark

---

## 10. Generation Parameters

Available parameters depend on the active model.

### Seed

The seed influences the random starting state of a generation. A fixed seed makes reproducible comparisons easier. Random mode creates different starting states for new runs.

### Steps

The number of denoising steps affects computation time and the result. More steps do not automatically produce a better image.

### CFG / Guidance

This value controls how strongly the generation follows the prompt. Extremely high values can reduce image quality.

### Resolution

Supported resolutions depend on the model and backend. Prefer the settings intended for the selected model.

### Sampler / Scheduler

Where supported by the active backend, the scheduler influences the denoising process. Not every combination is intended for every model.

---

## 11. Phoenix Boost

**Phoenix Boost** is a HK NPU STUDIO feature for improving or expanding prompts before image generation.

There are two fundamentally different modes.

### Deterministic Boost

The local deterministic boost works without an additional language model. It expands the prompt according to reproducible rules and can be used directly.

### AI Boost

The optional AI Boost uses a locally running language model to improve the prompt more intelligently.

RC2B uses:

- **Ollama** as the local model service
- **Qwen2.5 3B** as the intended local language model

If Ollama or Qwen is not yet available, Phoenix Boost guides you through the required setup. The model download may take some time.

After successful installation, this boost runs locally on the computer. The original prompt does not need to be sent to an external cloud prompt-optimization service.

### Boost Preview and Editing

Before the actual image generation, Phoenix Boost provides an interactive preview to review the optimized prompt.

- **Compact Preview:** An optimized, space-saving view displays the prompts in a structured layout.
- **Original/Optimized Prompt Side-by-Side:** The original and improved prompts are displayed side-by-side in a two-column view.
- **Negative Prompts Side-by-Side:** Negative prompts are also positioned side-by-side.
- **Fixed Action Bar:** The existing action buttons remain accessible outside the scroll area.
- **Scroll Fallback:** If the text is longer than the available space, a scroll area serves as a fallback to keep the content accessible.
- **Maximizable and Restorable:** The preview window can be maximized and restored to its original size.

> Phoenix Boost is optional. Normal image generation must not depend on Ollama or Qwen being installed.

---

## 12. ControlNet Canny

With supported model/backend combinations, **ControlNet Canny** can be used to preserve the structure of an existing image more strongly in a new generation.

Typical workflow:

1. Enable ControlNet Canny.
2. Select the source image.
3. Review the Canny preview.
4. Adjust edge thresholds if available.
5. Enter the prompt.
6. Start generation.

ControlNet is not available for every model variant. The interface adapts to the capabilities of the active model.

---

## 13. RealESRGAN NPU Upscaling

HK NPU STUDIO supports local **RealESRGAN upscaling on the NPU** to produce higher-resolution versions of existing images.

### 2× Upscaling

With **2× upscaling**, both the width and height of the source image are doubled. For example, a 512×512 image is output as a 1024×1024 image.

This mode is suitable for moderate enlargement when the source image should remain as close as possible to the original.

### 4× Upscaling

With **4× upscaling**, both the width and height of the source image are quadrupled. For example, a 512×512 image is output as a 2048×2048 image.

The 4× mode uses the designated RealESRGAN 4× path and processes larger images internally in tiles. The individual tiles are then recombined into the complete output image.

### Usage

1. Open the upscaling function in HK NPU STUDIO.
2. Select the source image.
3. Select **2×** or **4×** as the upscale factor.
4. Start the upscaling process.
5. Wait for local processing to complete.
6. Review the resulting image.

On supported Snapdragon PCs, upscaling runs locally through the designated NPU/QNN path. The source image is not sent to an external image-processing service.

> **Note:** Upscaling increases image resolution and reconstructs details. It is not a new prompt-based image generation. The goal is a higher-resolution version of the existing image while preserving the original image content as closely as possible.

---

## 14. Gallery, History, and Comparison

HK NPU STUDIO provides image and history views for reviewing generated images.

### Gallery and History

The gallery provides a structured overview of all locally generated images.

- **Search, Sorting, Thumbnail Size, and Filters:** You can search the gallery, sort images using the available criteria, adjust thumbnail size, and apply filters.
- **Open Output Folder:** This button opens the output folder configured for the current user in Windows Explorer. If the folder is missing, the application creates it safely.
- **Hover Preview:** The Phoenix switch "Hover Preview: On/Off" is located next to "Open Output Folder".
  - **Enabled by Default:** Hover preview is turned on by default.
  - **When On:** Hovering your mouse pointer over an image thumbnail in the gallery immediately opens the image preview.
  - **When Off:** Hovering over a thumbnail does not open a preview.
  - **Turning Off:** Disabling the function closes any currently open preview.
  - **Saved State:** The setting is persistently saved.
  - **Independence:** Image selection, double-clicking to open, and the context menu continue to work independently of this setting.

### Image Comparison and Metadata Validation

The integrated image comparison tool allows you to analyze two images side-by-side.

- **Loading Images:** You can load the original image and the output image side-by-side in the comparison view.
- **Zoom Options:** Zoom levels *Fit*, *50%*, *100%*, and *200%* are configured for the comparison view via the shared toolbar.
- **Panning:** When images are zoomed in, you can pan the section by holding down the left mouse button.
- **Synchronous Switch:**
  - When set to **Synchronous: On**, normalized pan positions are transferred to the other image (synchronized image positions).
  - When set to **Synchronous: Off**, the pan positions remain independent.
- **Swap:** You can instantly swap the positions of the two loaded images (left/right).
- **Compare Generation Metadata:** You can directly compare the embedded generation parameters (such as prompt, seed, steps, etc.) of both images.
  - *Important Clarification:* The metadata comparison is a purely text-based comparison of the technical generation parameters. It is **not** a visual pixel comparison, and **no** differing image areas are highlighted in color.
  - *Status Messages:* The application compares the metadata precisely and clearly distinguishes between:
    - *Missing metadata* (no metadata found in either image),
    - *One-sided metadata* (only one of the images contains metadata),
    - *Identical metadata* (both images were generated with exactly the same parameters),
    - *Differing metadata* (the parameters deviate from each other).

The exact presentation may continue to evolve between release candidates.

---

## 15. Language, Themes, and Windows Scaling

The user interface supports:

- German
- English
- Spanish

### Theme Options (Light & Dark)

A **Light Theme** and a **Dark Theme** are available. The language and theme can be changed at any time in the application settings. Theme parity ensures that all controls remain visually appealing and easily readable with high contrast in both color variants.

### Windows Scaling and Responsiveness

The Phoenix interface is optimized for Windows display scaling from **100% to 175%**.

- **Flexible Wrapping:** Control elements and action bars adapt dynamically to the window size and scaling. Automatic wrapping prevents buttons from being cut off.
- **Local Scroll Areas:** Scroll areas keep content and important actions accessible under high scaling or limited window height.

---

## 16. Local Data and Models

HK NPU STUDIO stores application settings, working data, and installed models locally.

With a normal installer installation, productive model data may be stored in the local application area of the Windows user, for example:

```text
%LOCALAPPDATA%\HK NPU STUDIO\models
```

Internal paths may differ between development and installer builds. **Do not manually move or delete model files** unless you are deliberately performing diagnostics.

The application validates model installations using expected files and metadata. A manually incomplete deletion or move can therefore cause a model to be detected as invalid.

---

## 17. Privacy and Offline Operation

A central goal of HK NPU STUDIO is local AI execution.

### Local

- Prompts are processed locally for image generation.
- Supported image models run locally on the PC.
- Generated images remain stored locally.
- Phoenix Boost runs locally after Ollama/Qwen setup.

### Internet Is Still Required for Some Setup Tasks

“Local” does not mean the entire setup can be completed without internet access. Downloads of application components, models, Qualcomm resources, Ollama, or Qwen initially require an internet connection.

After successful setup, the intended local generation functions can be used without a cloud image-generation service.

---

## 18. Troubleshooting

### A Model Is Shown as “Not Installed”

Open the Model Manager and use the intended installation workflow. Do not copy arbitrary model files into internal folders.

### Installation Was Interrupted

Restart HK NPU STUDIO and open the Model Manager. Depending on the model, Phoenix can reuse complete existing data or offer another download.

### SD3.5 Reports Incomplete Files

Use the setup or redownload option offered by Phoenix. The installer distinguishes between complete and incomplete Qualcomm output data and should not activate incomplete sources as a finished model.

### Qwen/Phoenix Boost Does Not Work Immediately After Installation

First verify that Ollama has fully started and Qwen2.5 3B is installed. If the local Ollama service has only just been set up, restarting the relevant application component may be necessary.

### Generation Takes a Long Time

Larger models and higher resolutions require more time. Preparation, first-time model loading, and overall system load also affect duration.

### The Application Appears Unresponsive

During long installation or generation phases, first wait for the displayed progress. Do not close the application during an active model download unless a clear error message is shown.

### Reporting an Error

For reproducible problems, the following information is helpful:

- HK NPU STUDIO version
- Windows version
- Snapdragon device/processor
- model in use
- exact steps leading to the problem
- relevant message or screenshot
- relevant log files, if available

---

## 19. Uninstalling

HK NPU STUDIO can be uninstalled through **Windows Settings → Apps → Installed apps**.

Note that large model files and user data may be stored separately depending on the installation and storage strategy. Before deleting anything manually, check whether you want to keep generated images or models.

---

## 20. FAQ

### Is HK NPU STUDIO an official Qualcomm product?

No. HK NPU STUDIO is an independent open-source project.

### Are my prompts sent to a cloud image service?

Supported image generation is designed for local execution. An internet connection is still required to download and set up some components.

### Do I need to install Python?

Not for normal use of the published Windows installer. Python 3.11 ARM64 is mainly relevant for development or running from source. SD3.5 setup manages its intended setup path through Phoenix.

### Do I need to install Ollama?

Only if you want to use the optional **Phoenix AI Boost**. Normal image generation should work without Ollama.

### Which language model does Phoenix AI Boost use?

RC2B uses **Qwen2.5 3B** through Ollama.

### Do I need to manually collect individual Qualcomm files for SD3.5?

The RC2B workflow is designed to automate Qualcomm setup as far as possible. Users should not need to manually select individual internal model components.

### Can I simply delete models from their folders?

This is not recommended during normal use. Use the intended management and installation workflows. Manual changes can temporarily cause stored state and actual files to differ.

### Which languages does the interface support?

German, English, and Spanish.

### Can I use HK NPU STUDIO on Intel or AMD PCs?

The project is designed for Windows 11 ARM64 on Snapdragon. Other platforms are not part of the officially intended or validated primary target.

---

## 21. Support and Bug Reports

Project repository:

`https://github.com/Kreuzhofen/hk-npu-studio`

For reproducible bugs, use GitHub Issues. For general questions and discussion, GitHub Discussions can be used if enabled for the repository.

Do not publish credentials, tokens, or other confidential information in logs or screenshots included with bug reports.

---

## 22. Open Source, Licenses, and Trademarks

HK NPU STUDIO is developed as an independent open-source project. The application itself is provided under the project license specified in the repository. Models, frameworks, and external components are additionally subject to their respective licenses and terms of use.

Qualcomm, Snapdragon, and Hexagon are trademarks or registered trademarks of Qualcomm Incorporated. Windows is a trademark of Microsoft. Other trademarks belong to their respective owners.

Use of these names describes technical platforms or compatibility and does not imply an official partnership or product affiliation.

---

## 23. RC2B at a Glance

RC2B focuses on a reliable and understandable user workflow, along with a modernized interface:

- **Guided Initial Setup:** Structured entry point for new users right from the first start.
- **Beginner-Friendly Model Manager:** The inspector remains scrollable while the model installation bar and its actions remain accessible.
- **Guided Model Sources and Downloads:** Automated Qualcomm QAI AppBuilder path for Stable Diffusion 3.5 Medium.
- **Automatic Activation:** Activation of the model immediately after successful installation and validation.
- **Status and Progress Displays:** Clear feedback during setup and generation.
- **Phoenix Boost with Optional AI Boost:** Intelligent prompt expansion via local Ollama/Qwen with a compact preview (maximizable/restorable, side-by-side prompts, sticky action bar, and scroll fallback).
- **RealESRGAN NPU Upscaling:** Local 2× and 4× upscaling of existing images through the designated NPU/QNN path.
- **Local Image Generation:** After the required setup, image generation runs locally on Windows 11 ARM64/Snapdragon. Internet access may still be required for setup and downloads.
- **Responsive Interface:** Optimized for Windows scaling from 100% to 175% with flexible wrapping and local scroll areas.
- **Reliable Output Folder:** Direct opening of the runtime path and safe automatic directory creation if it is missing.
- **Optional Gallery Hover Preview:** Image preview when hovering over gallery thumbnails (switch next to the output folder button, status is saved, disabling closes active preview).
- **Image Comparison and Synchronization:** Shared toolbar for zoom (Fit, 50%, 100%, 200%), panning with the left mouse button, and synchronized or independent panning (Synchronous On/Off).
- **Understandable Metadata Comparison:** Text-based comparison of parameters with clear status messages (no visual pixel comparison).

The goal remains deliberately simple:

> **Install HK NPU STUDIO → select a model → generate an image.**

---

**HK NPU STUDIO – Phoenix Engine**
Holger Kreuzhofen  
Founder & Lead Developer
