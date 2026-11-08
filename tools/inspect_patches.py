from PIL import Image
import numpy as np

im = Image.open("acceptance48_text_to_image.png")
arr = np.array(im)

# Let's inspect patch 1: (r=200..400, c=280..460) -> Where AAAAA is
patch_apple = arr[220:400, 290:460]
print("Patch Apple (220:400, 290:460):")
print("  R mean/min/max:", patch_apple[:,:,0].mean(), patch_apple[:,:,0].min(), patch_apple[:,:,0].max())
print("  G mean/min/max:", patch_apple[:,:,1].mean(), patch_apple[:,:,1].min(), patch_apple[:,:,1].max())
print("  B mean/min/max:", patch_apple[:,:,2].mean(), patch_apple[:,:,2].min(), patch_apple[:,:,2].max())

# Let's inspect patch 2: (r=50..150, c=50..150) -> Top left
patch_topleft = arr[50:150, 50:150]
print("\nPatch Top Left (50:150, 50:150):")
print("  R mean/min/max:", patch_topleft[:,:,0].mean(), patch_topleft[:,:,0].min(), patch_topleft[:,:,0].max())
print("  G mean/min/max:", patch_topleft[:,:,1].mean(), patch_topleft[:,:,1].min(), patch_topleft[:,:,1].max())
print("  B mean/min/max:", patch_topleft[:,:,2].mean(), patch_topleft[:,:,2].min(), patch_topleft[:,:,2].max())

# Let's inspect patch 3: (r=400..500, c=50..250) -> Table
patch_table = arr[400:500, 50:250]
print("\nPatch Table (400:500, 50:250):")
print("  R mean/min/max:", patch_table[:,:,0].mean(), patch_table[:,:,0].min(), patch_table[:,:,0].max())
print("  G mean/min/max:", patch_table[:,:,1].mean(), patch_table[:,:,1].min(), patch_table[:,:,1].max())
print("  B mean/min/max:", patch_table[:,:,2].mean(), patch_table[:,:,2].min(), patch_table[:,:,2].max())
