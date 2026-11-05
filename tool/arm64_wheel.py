"""Mark native Linux ARM64 wheels as platform-specific without a Python ABI."""

import platform
import shutil
import sys
from pathlib import Path

from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.install import install
from setuptools.command.sdist import sdist


def linux_arm64():
    return sys.platform == "linux" and platform.machine() == "aarch64"


class PlatformInstall(install):
    def finalize_options(self):
        if linux_arm64() and self.install_lib is None and self.install_platlib is not None:
            self.install_lib = self.install_platlib
        super().finalize_options()


class SourceDistribution(sdist):
    def make_distribution(self):
        self.filelist.append("tool/arm64_wheel.py")
        if linux_arm64():
            self.filelist.append("cef_binary/client/LICENSE.txt")
        super().make_distribution()


class PlatformWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self._linux_arm64 = linux_arm64()
        if self._linux_arm64:
            self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = super().get_tag()
        if self._linux_arm64:
            return self.python_tag, "none", plat
        return python, abi, plat

    def write_wheelfile(self, wheelfile_base, *args, **kwargs):
        super().write_wheelfile(wheelfile_base, *args, **kwargs)
        if self._linux_arm64:
            license_dir = Path(wheelfile_base) / "licenses"
            license_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile("cef_binary/client/LICENSE.txt", license_dir / "CEF-LICENSE.txt")
