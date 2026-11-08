from PIL import Image
import numpy as np

im = Image.open("acceptance48_text_to_image.png")
arr = np.array(im)

# Let's inspect the region directly above the apple top crest: Y in [170, 225], X in [330, 390]
crop_stem = arr[170:225, 330:390]
print(f"Crop stem shape: {crop_stem.shape}")

print("Region above apple crest (Y: 180 to 220):")
for y in range(180, 222, 2):
    row_rgb = arr[y, 340:385]
    # Find darkest pixel or characteristic stem color (stem is usually dark brown / green)
    lum = np.mean(row_rgb, axis=-1)
    min_x_offset = int(np.argmin(lum))
    stem_x = 340 + min_x_offset
    min_rgb = arr[y, stem_x]
    print(f"  y={y:3d}: darkest px at x={stem_x:3d} RGB={min_rgb} lum={lum[min_x_offset]:.1f}")
