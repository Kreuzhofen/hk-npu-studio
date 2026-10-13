# Third-Party Notices and Licenses

This package contains third-party model weights and derived components used for local AI photo restoration in HK NPU STUDIO.

---

## 1. FiDeSR

- **Component Name:** FiDeSR: High-Fidelity and Detail-Preserving One-Step Diffusion Super-Resolution
- **Upstream Repository:** Ar0Kim/FiDeSR (https://github.com/Ar0Kim/FiDeSR)
- **Model Weights:** jmjin2/FiDeSR (https://huggingface.co/jmjin2/FiDeSR)
- **License:** Apache License 2.0 (see `LICENSE-APACHE-2.0.txt`)
- **Notice:** FiDeSR LoRA/LRRB components are used as part of the Photo Restore model package.

---

## 2. Stable Diffusion 2.1 Base

- **Component Name:** Stable Diffusion 2.1 Base
- **Upstream:** Manojb/stable-diffusion-2-1-base / Stability AI SD 2.1
- **License:** CreativeML Open RAIL++-M License (see `LICENSE-CREATIVEML-OPENRAIL-M.txt`)
- **Notice:** UNet/VAE-derived components and empty prompt embeddings originate from or are derived from Stable Diffusion 2.1. Use of these components is subject to the CreativeML Open RAIL++-M license terms, including the Use Restrictions set forth in Attachment A.

---

## 3. Qualcomm Tooling and NPU Compilation Notice

- The model contexts were compiled for Qualcomm Snapdragon NPU / Hexagon HTP using Qualcomm AI Hub and QNN tooling.
- This package contains compiled model context binaries (`.serialized.bin.bin`) generated from the upstream model weights and does not include Qualcomm proprietary runtime libraries or SDK binaries.
- Reference to Qualcomm, Snapdragon, Hexagon, or QNN is solely descriptive of hardware compatibility and compilation tooling; this distribution does not claim or imply endorsement, sponsorship, certification, or joint authorship by Qualcomm Technologies, Inc. or any of its affiliates.

---

## 4. HK NPU STUDIO Distribution Notice

- HK NPU STUDIO distributes these third-party model components subject to their respective upstream licenses.
- No rights beyond those granted by the respective upstream licenses are conferred by HK NPU STUDIO for third-party model components.
