# Product Vision 2.0 – Snapdragon AI Studio

## 1. Mission

**Create. Organize. Review. Evolve.**

Snapdragon AI Studio is a professional, local AI Creative Suite designed specifically for Snapdragon-powered PCs. It leverages hardware acceleration (via Qualcomm Hexagon HPU/NPU) to make generative AI fast, accessible, and integrated.

---

## 2. Product Description

* **What it is:** A professional, local **AI Creative Suite** for generating, cataloging, evaluating, and automating generative media assets.
* **What it is NOT:** 
  * It is not a classical image editor (no brushes, no layer-blending, no traditional cropping).
  * It is not a pure upscaling utility (upscaling is just a pipeline tool).
  * It is not a Photoshop alternative. It focuses strictly on local generative AI workflows.

---

## 3. The Four Pillars (C.O.R.E.)

* **CREATE (AI Generate):** Direct parameter-based image and video generation powered by local NPUs.
* **ORGANIZE (AI Asset Library):** A central repository for generated assets, tracking metadata, prompts, and execution parameters.
* **REVIEW (Review Workspace):** Direct side-by-side quality and parameter comparison of generated assets.
* **EVOLVE (AI Workflow):** Advanced automation, pipeline cascading, batch tasks, and model management.

---

## 4. Workspace Concept

To reflect the transition into an AI Creative Suite, the workspaces follow a progressive naming scheme (current names continue to represent the active implementation state, while target names represent the long-term vision):

1. **Dashboard:** Unified control center, system state, and queue overview.
2. **AI Generate (Prompt Workspace):** The primary generation control panel for prompts and parameters.
3. **AI Asset Library (formerly Gallery):** Long-term goal for asset management, tagging, and history.
4. **Review Workspace (formerly Compare):** Long-term goal for side-by-side quality inspection.
5. **Asset Inspector (formerly Image Workspace):** Long-term goal for detailed single-asset parameter analysis.
6. **AI Model Manager:** Central hub for model discovery, local paths, and quantization states.
7. **Batch:** Bulk queue processing and background automation.

---

## 5. Architectural Principles

* **Commercial Quality:** Premium aesthetics (using HSL-based `ThemeManager`) and high resilience.
* **MVC Pattern:** Strict division of GUI presentation, controller routing, and generative model states.
* **Single Source of Truth:** Central parameter management (e.g. `GenerationSessionModel` and `GenerationQueue`).
* **Plugin First:** Modular interface for backends and workflow pipelines.
* **Local First:** Execution priority on local hardware (Snapdragon HPU/NPU via QNN SDK or local ONNX runtime fallfalls).

---

## 6. Out of Scope (What is NOT in the Product)

Snapdragon AI Studio intentionally excludes classic image editing tools to focus on generative workflows. The following are out of scope:
* Sharpening, Denoising, and traditional color filters.
* Curve adjustments and color correction layers.
* Selection brushes, clone stamps, or vector layers.
* RealESRGAN as a core feature. RealESRGAN serves purely as a technical Proof of Concept for QNN NPU tile-processing.

---

## 7. Official Roadmap

### Phase I: Foundation (Completed)
* Initial Phoenix layout, async thumbnail provider grid, and basic single-view rendering.
* Proof of concept QNN tile processing with RealESRGAN.
* HSL-based `ThemeManager` supporting Light & Dark modes.

### Phase II: AI Platform (Current & Mid-Term)
* **Model Manager:** Central model path resolving and configuration files.
* **Backend Discovery:** Automatic runtime detection (QNN, ONNX, CPU, Remote).
* **First AI Engine:** Local NPU text-to-image pipeline execution.
* **AI Asset Library:** Searchable history, prompt tagging, and collection organizer.
* **Review Workspace:** Synchronized pan/zoom before/after parameter comparison.
* **Asset Inspector:** Single-asset metadata inspector and parameters extraction.

### Phase III: AI Creative Suite (Long-Term Goal)
* Support for leading open-source models: **FLUX.1**, **SDXL**, **Stable Diffusion 3**, and video generation models (**Wan2.1**, **CogVideo**, **LTX Video**).
* **Workflow Automation:** Pipeline building (e.g., Generate -> Upscale -> Detail).
* **Plugin Ecosystem:** Community-submitted pipelines and third-party backend adapters.
