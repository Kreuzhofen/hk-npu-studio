#!/usr/bin/env python3
"""
Qualcomm Snapdragon SD2.1 QNN Execution Probe Tool.
CLI interface to trigger the QNN execution probe and display output/report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.qnn_execution_probe import main

if __name__ == "__main__":
    raise SystemExit(main())
