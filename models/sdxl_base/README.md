# sdxl-onnx-fp32

ONNX optimized version of **stabilityai/stable-diffusion-xl-base-1.0** with FP32 precision for maximum compatibility.

## Available Components
- **unet**: FP32 optimized
- **vae_decoder**: FP32 optimized
- **vae_encoder**: FP32 optimized
- **text_encoder**: FP32 optimized
- **text_encoder_2**: FP32 optimized

## Usage

### Basic CPU Usage
```python
from optimum.onnxruntime import ORTStableDiffusionPipeline

# Models use FP32 for maximum compatibility
pipe = ORTStableDiffusionPipeline.from_pretrained(
    "Mitchins/sdxl-onnx-fp32",
    provider="CPUExecutionProvider"
)

result = pipe("a red apple on a table")
result.images[0].save("output.png")
```

### GPU Usage (CUDA)
```python
pipe = ORTStableDiffusionPipeline.from_pretrained(
    "Mitchins/sdxl-onnx-fp32",
    provider="CUDAExecutionProvider"
)
```

## Performance Benefits
- **Compatibility**: Works reliably on CPU and GPU
- **Speed**: ONNX runtime optimizations
- **Stability**: No type mismatch issues
- **Quality**: Full FP32 precision

## File Structure
All models are FP32 for compatibility:

### unet/
- `model.onnx` (3.9MB + 9794.1MB data) - FP16 precision

### vae_decoder/
- `model.onnx` (188.9MB) - FP16 precision

### vae_encoder/
- `model.onnx` (130.4MB) - FP16 precision

### text_encoder/
- `model.onnx` (469.7MB) - FP16 precision

### text_encoder_2/
- `model.onnx` (0.8MB + 2649.9MB data) - FP16 precision


*Generated: 2025-08-08 11:05 UTC with onnxruntime 1.22.1*
