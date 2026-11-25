"""Static regression contract: OEM menu is additive and access is checked."""
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]
src=root/"app/src/main/java/ro/dj88bid/car"
class OemMenuContract(unittest.TestCase):
    def test_additive(self):
        main=(src/"MainActivity.kt").read_text()
        self.assertIn('FunctionTile("Setări auto","car"',main)
        self.assertIn('FunctionTile("OEM extins","oemextended"',main)
        self.assertIn('"oemextended" -> QfOemMenu.show(this@MainActivity)',main)
        self.assertIn('"car","canbus","maps","waze","youtube" -> Bridge().open(tile.key)',main)
    def test_safe_access(self):
        menu=(src/"QfOemMenu.java").read_text()
        for item in ('!info.exported','!info.enabled','checkSelfPermission(info.permission)','getActivityInfo','setPositiveButton("Deschide OEM"','resolve(a,ENTRIES[index])'):
            self.assertIn(item,menu)
        for item in ('sendBroadcast(', 'requestPermissions(', 'Settings.System.put', 'Runtime.getRuntime', 'bindService(', 'RPC_Send'):
            self.assertNotIn(item,menu)
    def test_manifest_targets(self):
        menu=(src/"QfOemMenu.java").read_text()
        for item in ('com.qf.backcar.FrontVdoActivity','com.qf.fancontrol.FanControlActivity','com.fvsm.camera.view.activity.GuideActivity','com.tpms.view.TpmsMainActivity','org.prowl.torque','com.qf.panelkeystudy.ui.PanelKeyStudyActivity','com.qf.keystudy.ui.KeyStudyActivity','com.zjinnova.android.zlink.features.launcher.AutoActivity'):
            self.assertIn(item,menu)
if __name__=="__main__":
    unittest.main()
