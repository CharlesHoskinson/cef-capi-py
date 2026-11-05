"""Check platform-specific wheel policy without building native binaries."""

import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


class PlatformWheelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.setuptools = importlib.import_module("setuptools")
        except ImportError as error:
            raise unittest.SkipTest("install the build dependency setuptools") from error
        path = Path(__file__).resolve().parents[1] / "tool" / "arm64_wheel.py"
        spec = importlib.util.spec_from_file_location("arm64_wheel", path)
        assert spec is not None and spec.loader is not None
        cls.backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.backend)

    def test_platform_detection(self):
        for system, machine, expected in (
            ("linux", "aarch64", True),
            ("linux", "x86_64", False),
            ("darwin", "arm64", False),
            ("win32", "AMD64", False),
        ):
            with (
                self.subTest(system=system, machine=machine),
                patch.object(sys, "platform", system),
                patch.object(self.backend.platform, "machine", return_value=machine),
            ):
                self.assertEqual(self.backend.linux_arm64(), expected)

    def test_non_arm_wheel_delegates_without_altering_tag(self):
        wheel = self.backend.PlatformWheel(self.setuptools.Distribution())
        wheel._linux_arm64 = False
        expected = ("py3", "none", "win_amd64")
        with patch.object(self.backend.bdist_wheel, "get_tag", return_value=expected):
            self.assertEqual(wheel.get_tag(), expected)

    def test_arm_wheel_preserves_platform_and_python_tags(self):
        wheel = self.backend.PlatformWheel(self.setuptools.Distribution())
        wheel._linux_arm64 = True
        wheel.python_tag = "py3"
        with patch.object(
            self.backend.bdist_wheel,
            "get_tag",
            return_value=("cp312", "cp312", "linux_aarch64"),
        ):
            self.assertEqual(wheel.get_tag(), ("py3", "none", "linux_aarch64"))


if __name__ == "__main__":
    unittest.main()
