"""Teste pentru inventarul read-only QF001."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from scan_qf001_apks import scan, hash_file


class ScannerTests(unittest.TestCase):
    def test_detects_radio_and_dsp_without_guessing_verified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "priv-app" / "QF_Radio").mkdir(parents=True)
            (root / "priv-app" / "QF_Radio" / "Radio.apk").write_bytes(b"test radio")
            (root / "app").mkdir()
            (root / "app" / "DSP.apk").write_bytes(b"test dsp")
            items = scan(root, None)
            self.assertEqual(len(items), 2)
            radio = next(x for x in items if x["relative_path"].endswith("Radio.apk"))
            self.assertIn("radio", radio["candidate_for"])
            self.assertFalse(radio["qf001_function_verified"])
            self.assertEqual(radio["manifest"]["status"], "aapt_indisponibil")
            dsp = next(x for x in items if x["relative_path"].endswith("DSP.apk"))
            self.assertIn("dsp", dsp["candidate_for"])
            self.assertFalse(dsp["qf001_function_verified"])

    def test_never_changes_input(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            apk = root / "Unknown.apk"
            apk.write_bytes(b"do not change")
            before = hash_file(apk)
            scan(root, None)
            self.assertEqual(before, hash_file(apk))
            self.assertEqual([x.name for x in root.iterdir()], ["Unknown.apk"])


if __name__ == "__main__":
    unittest.main()
