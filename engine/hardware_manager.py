"""
SnapdragonAI Studio

Hardware Manager

Created by Holger Kreuzhofen
Phoenix Engine
"""

import platform
import sys
import shutil
import ctypes


class HardwareManager:
    def get_system_info(self):
        return {
            "windows": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "Unbekannt",
            "python": sys.version.split()[0],
            "is_arm64": self.is_arm64(),
            "ram_gb": self.get_ram_gb(),
            "qnn_available": self.is_qnn_available(),
        }

    def is_arm64(self):
        return platform.machine().upper() in ["ARM64", "AARCH64"]

    def get_ram_gb(self):
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            memory_status = MEMORYSTATUSEX()
            memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status)):
                return round(memory_status.ullTotalPhys / (1024 ** 3), 1)

        except Exception:
            pass

        return "Unbekannt"

    def is_qnn_available(self):
        qnn_path = r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll"
        return shutil.os.path.exists(qnn_path)