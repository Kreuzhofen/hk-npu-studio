from PIL import Image
import numpy as np

im = Image.open("acceptance48_text_to_image.png")
arr = np.array(im)

# Search for green hue or green dominance near apple top: Y in [150, 250], X in [250, 450]
crop = arr[150:260, 250:450]
r = crop[:,:,0].astype(float)
g = crop[:,:,1].astype(float)
b = crop[:,:,2].astype(float)

# Leaf: Green channel significantly higher than Red and Blue, or greenish hue
green_leaf = (g > r + 10) & (g > b)
print("Green leaf candidates in top region:", np.sum(green_leaf))
if np.sum(green_leaf) > 0:
    ys, xs = np.where(green_leaf)
    print(f"Leaf region: X=[{250+xs.min()}, {250+xs.max()}], Y=[{150+ys.min()}, {150+ys.max()}]")
else:
    print("No distinct green leaf found. The fruit prompt was 'A photorealistic red apple on a wooden table...'.")
