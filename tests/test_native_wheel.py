"""Validate a built Linux ARM64 wheel without loading its native libraries.

Set CEF_ARM64_WHEEL to the wheel path before running this module.
"""

import os
import struct
import unittest
import zipfile
from pathlib import Path


@unittest.skipUnless(os.environ.get("CEF_ARM64_WHEEL"), "set CEF_ARM64_WHEEL")
class NativeWheelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ["CEF_ARM64_WHEEL"])
        cls.wheel = zipfile.ZipFile(cls.path)
        cls.addClassCleanup(cls.wheel.close)
        cls.names = set(cls.wheel.namelist())

    def test_platform_tag_and_metadata(self):
        self.assertTrue(self.path.name.endswith("-linux_aarch64.whl"))
        metadata = [name for name in self.names if name.endswith(".dist-info/WHEEL")]
        self.assertEqual(len(metadata), 1)
        contents = self.wheel.read(metadata[0]).decode("utf-8")
        self.assertIn("Root-Is-Purelib: false", contents)
        self.assertIn("Tag: py3-none-linux_aarch64", contents)

    def test_runtime_and_bindings_are_packaged(self):
        for name in (
            "cef_capi/linux_aarch64/header.py",
            "cef_capi/linux_aarch64/struct.py",
            "cef_capi/runtime/libcef.so",
            "cef_capi/runtime/cefsimple",
            "cef_capi/runtime/icudtl.dat",
            "cef_capi/runtime/resources.pak",
            "cef_capi/runtime/locales/en-US.pak",
        ):
            with self.subTest(name=name):
                self.assertIn(name, self.names)
        mode = self.wheel.getinfo("cef_capi/runtime/cefsimple").external_attr >> 16
        self.assertNotEqual(mode & 0o111, 0, "cefsimple must be executable")

    def test_cef_license_is_packaged(self):
        notices = [
            name for name in self.names
            if name.endswith(".dist-info/licenses/CEF-LICENSE.txt")
        ]
        self.assertEqual(len(notices), 1)
        notice = self.wheel.read(notices[0])
        self.assertTrue(notice)
        client_license = os.environ.get("CEF_CLIENT_LICENSE")
        if client_license:
            self.assertEqual(notice, Path(client_license).read_bytes())

    def test_native_elf_machine(self):
        binaries = []
        for name in self.names:
            if not name.startswith("cef_capi/runtime/") or name.endswith("/"):
                continue
            with self.wheel.open(name) as binary:
                elf = binary.read(20)
            if elf.startswith(b"\x7fELF"):
                binaries.append(name)
                with self.subTest(name=name):
                    self.assertEqual(elf[:6], b"\x7fELF\x02\x01", name)
                    self.assertEqual(struct.unpack_from("<H", elf, 18)[0], 183, name)
        self.assertIn("cef_capi/runtime/libcef.so", binaries)
        self.assertIn("cef_capi/runtime/cefsimple", binaries)


if __name__ == "__main__":
    unittest.main()
