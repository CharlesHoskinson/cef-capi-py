"""Run the installed CEF local-page screenshot smoke test on demand.

Set CEF_RUNTIME_PYTHON to an environment containing the wheel. Set LD_PRELOAD
before starting this test when the host requires the ARM64 TLS workaround.
The test needs a working X11 display.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.environ.get("CEF_RUNTIME_PYTHON"), "set CEF_RUNTIME_PYTHON")
class NativeRuntimeTest(unittest.TestCase):
    def test_local_page_screenshot_and_javascript(self):
        python = Path(os.environ["CEF_RUNTIME_PYTHON"]).absolute()
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        with tempfile.TemporaryDirectory() as directory:
            env["XDG_CONFIG_HOME"] = str(Path(directory) / "config")
            env["XDG_CACHE_HOME"] = str(Path(directory) / "cache")
            result = subprocess.run(
                [str(python), "-u", "-m", "cef_capi.smoke_test"],
                cwd=directory,
                env=env,
                capture_output=True,
                text=True,
                timeout=55,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cef-capi-py smoke test OK.", result.stdout)


if __name__ == "__main__":
    unittest.main()
