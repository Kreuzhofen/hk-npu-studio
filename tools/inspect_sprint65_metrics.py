import json

with open('reports/phoenix_material_lab_65/phoenix_material_lab_65_metrics.json', 'r') as f:
    metrics = json.load(f)

print(f"Total metrics records: {len(metrics)}")

motives = ['m1_glass', 'm2_ceramic', 'm3_metal', 'm4_wood_plastic']
materials = ['24k_gold', 'antique_brass', 'copper', 'chrome']

print("\n=== HTP REFINEMENT RESULTS (QUALCOMM HEXAGON HTP V73) ===")
for m in motives:
    print(f"\nMotive: {m}")
    for mat in materials:
        k = f"htp_{m}_{mat}"
        rec = metrics.get(k)
        if rec:
            pm_name = rec['primary_metric']['name']
            pm_val = rec['primary_metric']['value_pct']
            cm = rec['color_metrics']
            bg = rec['feathered_mask_bg_identity_pct']
            nb = rec['neighbor_mse']
            lat = rec['inference_latency_seconds']
            cpu = rec['cpu_fallback_ms']
            print(f"  {mat:13s}: {pm_name} = {pm_val:5.2f}% | Sat = {cm['mean_sat']:.2f} | Bg-Id = {bg:.4f}% | Neigh MSE = {nb:.6f} | Lat = {lat:5.2f}s | CPU = {cpu}ms")

print("\n=== CHROME DEEP DIVE COMPARISON (ALL 4 MOTIVES) ===")
for m in motives:
    p50 = metrics.get(f"priming_{m}_chrome_50", {}).get("primary_metric", {}).get("value_pct", 0.0)
    p75 = metrics.get(f"priming_{m}_chrome_75", {}).get("primary_metric", {}).get("value_pct", 0.0)
    p100 = metrics.get(f"priming_{m}_chrome_100", {}).get("primary_metric", {}).get("value_pct", 0.0)
    htp = metrics.get(f"htp_{m}_chrome", {})
    h_val = htp.get("primary_metric", {}).get("value_pct", 0.0)
    h_spec = htp.get("color_metrics", {}).get("chrome_specular_pct", 0.0)
    h_sat = htp.get("color_metrics", {}).get("mean_sat", 0.0)
    print(f"  {m:15s}: Priming 50%={p50:5.2f}% | 75%={p75:5.2f}% | 100%={p100:5.2f}% || HTP={h_val:5.2f}% (Specular={h_spec:5.2f}%, Sat={h_sat:.2f})")
