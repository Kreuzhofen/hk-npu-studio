from PIL import Image
import numpy as np

im = Image.open("acceptance48_text_to_image.png")
arr = np.array(im)
h, w, _ = arr.shape

# Let's inspect 8x8 blocks across the image
grid_h, grid_w = 16, 16
bh, bw = h // grid_h, w // grid_w

print("Average RGB across 16x16 grid:")
for r in range(grid_h):
    row_str = []
    for c in range(grid_w):
        block = arr[r*bh:(r+1)*bh, c*bw:(c+1)*bw]
        mr, mg, mb = np.mean(block, axis=(0,1)).astype(int)
        # determine dominant character: A (Apple red), T (Table light), W (Wood dark/warm)
        if mr > 120 and mr > mg + 50 and mr > mb + 50:
            char = "A" # Bright red Apple
        elif mr > 60 and mr > mg + 30 and mr > mb + 30:
            char = "a" # Darker red Apple
        elif mg > 140 and mb > 130:
            char = "T" # Table highlight
        elif mr > mg and mr > mb:
            char = "w" # Wood warm
        else:
            char = "."
        row_str.append(char)
    print(f"Row {r:02d}: " + "".join(row_str))
