"""
PyInstaller Runtime Hook for Windows ARM64 Standalone.
Ensures setuptools._vendor.backports is mapped to sys.modules['backports']
prior to pkg_resources or jaraco initialization.
"""
import sys

try:
    import setuptools._vendor.backports as _bp
    sys.modules['backports'] = _bp
    import setuptools._vendor.backports.tarfile as _bpt
    sys.modules['backports.tarfile'] = _bpt
except Exception:
    pass
