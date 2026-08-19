# Snapdragon AI Studio – Phoenix Engine
## User Guide – Version 2.0 RC2A

> **Independent open-source project for Windows on Snapdragon.**  
> Snapdragon AI Studio is not an official product of Qualcomm Technologies, Inc. and is not sponsored or supported by Qualcomm.

---

## 1. Welcome

Snapdragon AI Studio is a desktop application for local AI image generation on Windows 11 ARM64 PCs with Snapdragon processors. The **Phoenix Engine** manages model handling, preparation, and execution of the supported AI pipelines.

RC2A puts particular emphasis on a guided workflow: **Install → select a model → generate an image.** Technical details should remain in the background as much as possible during normal use.

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

## 3. Installing RC2A

1. Download the current ARM64 installer from the official Snapdragon AI Studio GitHub release.
2. Start `SnapdragonAIStudio-2.0.0-rc.2a-ARM64-Setup.exe`.
3. Follow the Windows setup wizard.
4. Start **Snapdragon AI Studio** from the Start menu or the created shortcut.

> **Windows SmartScreen:** Windows may display a warning for a release that is not widely recognized or commercially signed. Only use installers obtained from the official project repository.

A separate Python installation is not required for normal use of the published installer.

---

## 4. First Start

RC2A guides new users through initial setup much more clearly than earlier release candidates.

The home page shows the current setup state. If no usable model has been configured yet, the application guides you to the Model Manager. After successful setup, the readiness status is updated and you can proceed directly to your first image generation.

### Basic Workflow

1. Start Snapdragon AI Studio.
2. Open the Model Manager.
3. Select the desired supported model.
4. Start the offered installation workflow.
5. Allow installation and validation to complete.
6. Activate the model or wait for automatic activation.
7. Switch to image generation.

For the normal guided workflow, you do not need to select individual internal ONNX, QNN, or model components.

---

## 5. Model Manager

The Model Manager displays the models known to Snapdragon AI Studio and their current state.

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

RC2A uses different sources and installation methods depending on the model. The Model Manager attempts to hide these differences and provide a guided workflow.

### Stable Diffusion 1.5

Stable Diffusion 1.5 is a compact entry point for local image generation and is particularly suitable for fast 512×512 workflows. With a supported NPU variant, Phoenix handles the required package validation and activation.

### Stable Diffusion 2.1

Stable Diffusion 2.1 is also available as a Snapdragon/Qualcomm-oriented image-generation path. Installation and activation are handled through the Model Manager according to the source configured for the model.

### Stable Diffusion 3.5 Medium

RC2A includes a substantially more automated setup path for **Stable Diffusion 3.5 Medium via Qualcomm QAI AppBuilder**. This workflow is described separately in the next section.

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
6. import the generated files into Snapdragon AI Studio,
7. create the manifest and validation information,
8. validate the installation,
9. activate the model afterwards.

The installation window displays the current step and progress throughout the process.

### Qualcomm QAI AppBuilder

This setup path uses Qualcomm's official QAI AppBuilder project. Phoenix searches for the expected ZIP archive in the Downloads folder. If it cannot be found automatically, the application can ask you to select the ZIP archive.

The ZIP file itself is not deleted as a user file by the normal installation process.

### Model Download

During setup, the Qualcomm script downloads the required SD3.5 files. The download is currently approximately **3.24 GB**. Speed and duration depend on the internet connection, storage device, and system state.

Do not close Snapdragon AI Studio during this process; allow the installation to complete.

### Completion

After setup, the model files are validated and the model becomes available to Snapdragon AI Studio. The successful RC2A user workflow was tested as a complete chain:

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

**Phoenix Boost** is a Snapdragon AI Studio feature for improving or expanding prompts before image generation.

There are two fundamentally different modes.

### Deterministic Boost

The local deterministic boost works without an additional language model. It expands the prompt according to reproducible rules and can be used directly.

### AI Boost

The optional AI Boost uses a locally running language model to improve the prompt more intelligently.

RC2A uses:

- **Ollama** as the local model service
- **Qwen2.5 3B** as the intended local language model

If Ollama or Qwen is not yet available, Phoenix Boost guides you through the required setup. The model download may take some time.

After successful installation, this boost runs locally on the computer. The original prompt does not need to be sent to an external cloud prompt-optimization service.

### Preview

Before image generation, you can review the prompt version produced by Phoenix Boost. This makes it clear which description is actually passed to the image pipeline.

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

## 13. Gallery, History, and Comparison

Snapdragon AI Studio provides image and history views for reviewing generated images.

Depending on the view, you can:

- review previous generations,
- reopen results,
- compare images,
- inspect relevant generation information.

The exact presentation may continue to evolve between release candidates.

---

## 14. Language, Dark Mode, and Light Mode

The user interface supports:

- German
- English
- Spanish

Dark and Light appearances are also available. Language and appearance can be changed in the application settings.

---

## 15. Local Data and Models

Snapdragon AI Studio stores application settings, working data, and installed models locally.

With a normal installer installation, productive model data may be stored in the local application area of the Windows user, for example:

```text
%LOCALAPPDATA%\Snapdragon AI Studio\models
```

Internal paths may differ between development and installer builds. **Do not manually move or delete model files** unless you are deliberately performing diagnostics.

The application validates model installations using expected files and metadata. A manually incomplete deletion or move can therefore cause a model to be detected as invalid.

---

## 16. Privacy and Offline Operation

A central goal of Snapdragon AI Studio is local AI execution.

### Local

- Prompts are processed locally for image generation.
- Supported image models run locally on the PC.
- Generated images remain stored locally.
- Phoenix Boost runs locally after Ollama/Qwen setup.

### Internet Is Still Required for Some Setup Tasks

“Local” does not mean the entire setup can be completed without internet access. Downloads of application components, models, Qualcomm resources, Ollama, or Qwen initially require an internet connection.

After successful setup, the intended local generation functions can be used without a cloud image-generation service.

---

## 17. Troubleshooting

### A Model Is Shown as “Not Installed”

Open the Model Manager and use the intended installation workflow. Do not copy arbitrary model files into internal folders.

### Installation Was Interrupted

Restart Snapdragon AI Studio and open the Model Manager. Depending on the model, Phoenix can reuse complete existing data or offer another download.

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

- Snapdragon AI Studio version
- Windows version
- Snapdragon device/processor
- model in use
- exact steps leading to the problem
- relevant message or screenshot
- relevant log files, if available

---

## 18. Uninstalling

Snapdragon AI Studio can be uninstalled through **Windows Settings → Apps → Installed apps**.

Note that large model files and user data may be stored separately depending on the installation and storage strategy. Before deleting anything manually, check whether you want to keep generated images or models.

---

## 19. FAQ

### Is Snapdragon AI Studio an official Qualcomm product?

No. Snapdragon AI Studio is an independent open-source project.

### Are my prompts sent to a cloud image service?

Supported image generation is designed for local execution. An internet connection is still required to download and set up some components.

### Do I need to install Python?

Not for normal use of the published Windows installer. Python 3.11 ARM64 is mainly relevant for development or running from source. SD3.5 setup manages its intended setup path through Phoenix.

### Do I need to install Ollama?

Only if you want to use the optional **Phoenix AI Boost**. Normal image generation should work without Ollama.

### Which language model does Phoenix AI Boost use?

RC2A uses **Qwen2.5 3B** through Ollama.

### Do I need to manually collect individual Qualcomm files for SD3.5?

The RC2A workflow is designed to automate Qualcomm setup as far as possible. Users should not need to manually select individual internal model components.

### Can I simply delete models from their folders?

This is not recommended during normal use. Use the intended management and installation workflows. Manual changes can temporarily cause stored state and actual files to differ.

### Which languages does the interface support?

German, English, and Spanish.

### Can I use Snapdragon AI Studio on Intel or AMD PCs?

The project is designed for Windows 11 ARM64 on Snapdragon. Other platforms are not part of the officially intended or validated primary target.

---

## 20. Support and Bug Reports

Project repository:

`https://github.com/Kreuzhofen/snapdragon-ai-studio`

For reproducible bugs, use GitHub Issues. For general questions and discussion, GitHub Discussions can be used if enabled for the repository.

Do not publish credentials, tokens, or other confidential information in logs or screenshots included with bug reports.

---

## 21. Open Source, Licenses, and Trademarks

Snapdragon AI Studio is developed as an independent open-source project. The application itself is provided under the project license specified in the repository. Models, frameworks, and external components are additionally subject to their respective licenses and terms of use.

Qualcomm, Snapdragon, and Hexagon are trademarks or registered trademarks of Qualcomm Incorporated. Windows is a trademark of Microsoft. Other trademarks belong to their respective owners.

Use of these names describes technical platforms or compatibility and does not imply an official partnership or product affiliation.

---

## 22. RC2A at a Glance

RC2A focuses particularly on a more reliable and understandable user workflow:

- guided initial setup,
- beginner-friendly Model Manager,
- guided model sources and downloads,
- automatic activation after successful installation,
- improved status and progress displays,
- Phoenix Boost with optional local AI Boost,
- automated Qualcomm QAI AppBuilder path for Stable Diffusion 3.5 Medium,
- local image generation on Windows 11 ARM64 / Snapdragon.

The goal remains deliberately simple:

> **Install Snapdragon AI Studio → select a model → generate an image.**

---

**Snapdragon AI Studio – Phoenix Engine**  
Holger Kreuzhofen  
Founder & Lead Developer
