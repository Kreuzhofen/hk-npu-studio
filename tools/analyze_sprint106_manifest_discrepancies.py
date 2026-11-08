"""
Forensic analysis of Sprint 105 Dependency Manifest and QNN binary size discrepancies.
"""
import importlib.metadata
import importlib.util
import json
from pathlib import Path

spec = importlib.util.find_spec('onnxruntime_qnn')
qnn_dir = Path(spec.origin).resolve().parent
files = sorted(qnn_dir.glob('*'))
total_bytes = 0
v73_relevant_bytes = 0
v73_only_bytes = 0

print(f"Directory: {qnn_dir}\n")
print(f"{'Filename':<32} {'Bytes':>14} {'MB (1024^2)':>12} {'MB (10^6)':>12}")
print("-" * 74)

for f in files:
    if f.suffix.lower() in ('.dll', '.so', '.bin'):
        sz = f.stat().st_size
        total_bytes += sz
        mb_bin = sz / (1024 * 1024)
        mb_dec = sz / 1_000_000
        is_v68 = 'v68' in f.name.lower()
        is_v81 = 'v81' in f.name.lower()
        if not is_v68:
            v73_relevant_bytes += sz
        if not is_v68 and not is_v81:
            v73_only_bytes += sz
        print(f"{f.name:<32} {sz:>14,d} {mb_bin:>12.2f} {mb_dec:>12.2f}")

print("-" * 74)
print(f"{'TOTAL (All 16 files)':<32} {total_bytes:>14,d} {total_bytes/(1024*1024):>12.2f} {total_bytes/1000000:>12.2f}")
print(f"{'Without V68 (14 files)':<32} {v73_relevant_bytes:>14,d} {v73_relevant_bytes/(1024*1024):>12.2f} {v73_relevant_bytes/1000000:>12.2f}")
print(f"{'V73 Target Only (12 files)':<32} {v73_only_bytes:>14,d} {v73_only_bytes/(1024*1024):>12.2f} {v73_only_bytes/1000000:>12.2f}")

print("\n=== Dependency Manifest Analysis ===")
system_site = Path("C:/Program Files/Python311-arm64/Lib/site-packages")
user_site = Path(r"C:\Users\holge\AppData\Roaming\Python\Python311-arm64\site-packages")

sys_dists = [d.metadata["Name"] for d in importlib.metadata.distributions(path=[str(system_site)])]
user_dists = [d.metadata["Name"] for d in importlib.metadata.distributions(path=[str(user_site)])]

print(f"System site distributions ({len(sys_dists)}): {sys_dists}")
print(f"User site distributions ({len(user_dists)}):")

# Load Sprint 105 dependency_manifest.json
manifest_path = Path("reports/sprint_105_packaging_audit/dependency_manifest.json")
if manifest_path.exists():
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    print("\nSprint 105 Manifest counts:")
    print(json.dumps(m["dependency_audit"]["counts"], indent=2))
    print(f"Report stated: 10 Core + 42 Transitive + 22 Dev-Tools = 74 (or 73 user + 1 sys)")
    print(f"Manifest has: direct: {m['dependency_audit']['counts']['direct']} (user-only, omitting Pillow from system), transitive: {m['dependency_audit']['counts']['transitive']}, dev_tools: {m['dependency_audit']['counts']['dev_tools']}")
    print(f"Sum in manifest: 9 + 44 + 20 = 73 user packages.")
