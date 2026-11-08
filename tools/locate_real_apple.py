from PIL import Image, ImageFilter
import numpy as np

im = Image.open("acceptance48_text_to_image.png")
arr = np.array(im, dtype=float)
r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

# Apple criterion:
# R is significantly higher than G and B
diff = (r - np.maximum(g, b))
print(f"Max (R - max(G,B)): {diff.max():.1f}, mean: {diff.mean():.1f}")

# Threshold for red apple
red_mask = (diff > 45.0) & (r > 80.0)

# Clean up with PIL morphological filters
mask_img = Image.fromarray((red_mask.astype(np.uint8) * 255), mode="L")
# Close small holes
mask_closed = mask_img.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
mask_np = np.array(mask_closed) > 128

# Connected components using disjoint-set or simple BFS
h, w = mask_np.shape
visited = np.zeros((h, w), dtype=bool)

components = []
for y in range(h):
    for x in range(w):
        if mask_np[y, x] and not visited[y, x]:
            comp = []
            queue = [(y, x)]
            visited[y, x] = True
            while queue:
                cy, cx = queue.pop()
                comp.append((cy, cx))
                for ny, nx in ((cy-1, cx), (cy+1, cx), (cy, cx-1), (cy, cx+1)):
                    if 0 <= ny < h and 0 <= nx < w:
                        if mask_np[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((ny, nx))
            components.append(comp)

components.sort(key=len, reverse=True)
print(f"Total components found: {len(components)}")
for i, comp in enumerate(components[:5]):
    ys = [p[0] for p in comp]
    xs = [p[1] for p in comp]
    print(f"Component {i}: size={len(comp)}, BBox X=[{min(xs)}, {max(xs)}], Y=[{min(ys)}, {max(ys)}], Centroid=({np.mean(xs):.1f}, {np.mean(ys):.1f})")
