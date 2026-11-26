import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("body",Path(__file__).resolve().parents[1]/"tools/qf_body_share.py")
body=importlib.util.module_from_spec(spec)
spec.loader.exec_module(body)

class TestBodyShare(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.backup=Path(tmp.name)/"backup.json"
        self.state={body.REGISTRY:"com.oem.launcher",body.KEY:"null"}
        self.writes=[]
        self.has_oem=True
        p=patch.object(body,"adb",side_effect=self.fake)
        p.start(); self.addCleanup(p.stop)
    def fake(self,serial,*args):
        if args==("get-state",): return "device"
        if args[:3]==("shell","pm","path"):
            return "" if args[-1]==body.OEM and not self.has_oem else "package:/test.apk"
        k=args[4]; self.assertIn(k,body.KEYS)
        if args[2]=="get": return self.state[k]
        if args[2]=="put": self.state[k]=args[5] if args[5]!="''" else ""
        elif args[2]=="delete": self.state[k]="null"
        else: self.fail(str(args))
        self.writes.append(args); return ""
    def run_action(self,action,serial="QF"):
        return body.execute(serial,action,self.backup)
    def test_check(self):
        self.assertEqual(self.run_action("check"),self.state)
        self.assertFalse(self.writes)
    def test_enable_and_restore(self):
        original=self.state.copy()
        self.run_action("enable")
        self.assertEqual(self.state[body.REGISTRY],"com.oem.launcher,"+body.PACKAGE)
        self.assertEqual(self.state[body.KEY],"1")
        self.run_action("restore")
        self.assertEqual(self.state,original)
    def test_absent_registry(self):
        self.state[body.REGISTRY]="null"
        self.run_action("enable")
        self.assertEqual(self.state[body.REGISTRY],body.PACKAGE)
        self.run_action("restore")
        self.assertEqual(self.state[body.REGISTRY],"null")
    def test_flag_alone_not_enough(self):
        self.state[body.KEY]="1"
        self.run_action("enable")
        self.assertIn(body.PACKAGE,self.state[body.REGISTRY].split(","))
    def test_already_registered(self):
        self.state={body.REGISTRY:"com.oem.launcher,"+body.PACKAGE,body.KEY:"1"}
        self.run_action("enable");self.assertFalse(self.writes)
    def test_other_device(self):
        self.run_action("enable")
        with self.assertRaises(RuntimeError): self.run_action("restore","OTHER")
    def test_concurrent_client(self):
        self.run_action("enable")
        self.state[body.REGISTRY]+=",com.other.launcher"
        with self.assertRaises(RuntimeError): self.run_action("restore")
        self.assertIn("com.other.launcher",self.state[body.REGISTRY])
    def test_no_oem(self):
        self.has_oem=False
        with self.assertRaises(RuntimeError): self.run_action("enable")
        self.assertFalse(self.writes)
    def test_backup_exists(self):
        self.backup.write_text("old")
        with self.assertRaises(FileExistsError): self.run_action("enable")
        self.assertFalse(self.writes)
    def test_unknown_registry(self):
        self.state[body.REGISTRY]="bad registry"
        with self.assertRaises(RuntimeError): self.run_action("enable")
        self.assertFalse(self.writes)

if __name__=="__main__":
    unittest.main()
