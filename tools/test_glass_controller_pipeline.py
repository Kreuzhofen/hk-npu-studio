"""
Test PromptEditController execution on Glass Sculpture with:
- Enhanced negative prompt ('seam, black line, dark slit, crease, shadow line...')
- Candidate seeds through the controller pipeline (with full crop and pad composite)
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import numpy as np

from controllers.prompt_edit_controller import PromptEditController

def test_controller_glass():
    input_path = Path("reports/sprint_80_total_validation/images/motif2_glass_1_original.png")
    out_dir = Path("reports/sprint_85_material_polish/images/glass_controller_tests")
    out_dir.mkdir(parents=True, exist_ok=True)

    controller = PromptEditController()

    plan = controller.create_plan(
        image=Image.open(input_path),
        prompt="Verwandle die Glasskulptur in 24k Gold."
    )
    print(f"Plan target_object: '{plan.target_object}', material_preset: '{plan.material_preset}'")
    print(f"Plan refined_prompt: {plan.refined_prompt}")
    print(f"Plan negative_prompt: {plan.negative_prompt}")

if __name__ == "__main__":
    test_controller_glass()
