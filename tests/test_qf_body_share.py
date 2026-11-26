import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("body", Path(__file__).resolve().parents[1] / "tools/qf_body_share.py")
body = importlib.util.module_from_spec(spec)
spec.loader.exec_module(body)

class TestBodyShare(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.backup = Path(self.tmp.name) / "backup.json"
        self.state = "null"
        self.writes = []
        self.has_oem = True
        self.patcher = patch.object(body, "adb", side_effect=self.fake)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
    def fake(self, serial, *args):
        if args == ("get-state",):
            return "device"
        if args[:3] == ("shell", "pm", "path"):
            if args[-1] == body.OEM and not self.has_oem:
                return ""
            return "package:/system/test.apk"
        if args[:4] == ("shell", "settings", "get", "global"):
            self.assertEqual(args[4], body.KEY)
            return self.state
        if args[:4] == ("shell", "settings", "put", "global"):
            self.assertEqual(args[4], body.KEY)
            self.state = args[5]
        elif args[:4] == ("shell", "settings", "delete", "global"):
            self.assertEqual(args[4], body.KEY)
            self.state = "null"
        else:
            self.fail(str(args))
        self.writes.append(args)
        return ""
    def test_check_no_write(self):
        self.assertEqual(body.execute("QF", "check", self.backup), "null")
        self.assertFalse(self.writes)
        self.assertFalse(self.backup.exists())
    def test_enable_and_restore_absent(self):
        self.assertEqual(body.execute("QF", "enable", self.backup), "1")
        self.assertEqual(body.execute("QF", "restore", self.backup), "null")
    def test_restore_disabled(self):
        self.state = "0"
        body.execute("QF", "enable", self.backup)
        self.assertEqual(body.execute("QF", "restore", self.backup), "0")
    def test_already_enabled_no_write(self):
        self.state = "1"
        body.execute("QF", "enable", self.backup)
        self.assertFalse(self.writes)
    def test_other_device_cannot_restore(self):
        body.execute("QF", "enable", self.backup)
        with self.assertRaises(RuntimeError):
            body.execute("OTHER", "restore", self.backup)
        self.assertEqual(len(self.writes), 1)
    def test_missing_oem_refused(self):
        self.has_oem = False
        with self.assertRaises(RuntimeError):
            body.execute("QF", "enable", self.backup)
        self.assertFalse(self.writes)
    def test_existing_backup_not_overwritten(self):
        self.backup.write_text("old")
        with self.assertRaises(FileExistsError):
            body.execute("QF", "enable", self.backup)
        self.assertFalse(self.writes)
    def test_unknown_value_refused(self):
        self.state = "unexpected"
        with self.assertRaises(RuntimeError):
            body.execute("QF", "enable", self.backup)
        self.assertFalse(self.writes)

if __name__ == "__main__":
    unittest.main()
