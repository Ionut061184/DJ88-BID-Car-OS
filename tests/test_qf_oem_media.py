"""Source contract: OEM component routing. Physical availability remains unverified."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
K=(ROOT/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
M=ET.parse(ROOT/"app/src/main/AndroidManifest.xml").getroot()
class TestOemMedia(unittest.TestCase):
    def test_exact_manifest_components(self):
        for action,pkg,activity in [
            ("radio","com.android.fmradio.ext","com.android.fmradio.FmMainActivity"),
            ("dsp","com.qf.soundeffect","com.qf.soundeffect.SoundActivity"),
            ("btcar","com.qf.bluetooth","com.qf.bluetooth.BluetoothActivity"),
            ("btmusic","com.qf.bluetooth","com.qf.bluetooth.MusicActivity"),
            ("steering","com.qf.keystudy","com.qf.keystudy.ui.KeyStudyActivity"),
            ("panelkeys","com.qf.panelkeystudy","com.qf.panelkeystudy.ui.PanelKeyStudyActivity")]:
            self.assertIn(f'"{action}" to Pair("{pkg}", "{activity}")',K)
            self.assertIn(pkg,[x.attrib.get("{http://schemas.android.com/apk/res/android}name") for x in M.findall("queries/package")])
    def test_exact_activity_precedes_package_fallback(self):
        f=K.split("private fun originalQf001Intent",1)[1].split("private fun assignedIntent",1)[0]
        self.assertLess(f.index("if (accessible(explicit))"),f.index("getLaunchIntentForPackage"))
        self.assertIn('setOf("btcar", "btmusic", "steering", "panelkeys")) return null',f)
        self.assertIn("info.exported",f)
        self.assertIn("checkPermission",f)
    def test_drawer_distinguishes_phone_music_and_keys(self):
        for label,route in [("Bluetooth / Telefon","btaudio"),("Muzică Bluetooth","btmusic"),("Comenzi volan","steering"),("Butoane panou","panelkeys")]:
            self.assertIn(f'FunctionTile("{label}","{route}"',K)
        self.assertIn('kind in setOf("btmusic", "steering", "panelkeys")',K)
    def test_original_utilities_and_projection(self):
        for action,pkg,activity in [
            ("gps","com.qf.beidougps","com.qf.beidougps.BeidouGpsActivity"),
            ("gpstest","com.chartcross.gpstest","com.chartcross.gpstest.MainActivity"),
            ("tpms","com.syt.tmps","com.tpms.view.TpmsMainActivity"),
            ("files","com.sprd.fileexplorer","com.sprd.fileexplorer.activities.FileExploreActivity"),
            ("zlink","com.zjinnova.zlink","com.zjinnova.android.zlink.features.main.MainActivity"),
            ("carplay","com.zjinnova.zlink","com.zjinnova.android.zlink.features.launcher.CarPlayActivity"),
            ("androidauto","com.zjinnova.zlink","com.zjinnova.android.zlink.features.launcher.AutoActivity"),
            ("hicar","com.zjinnova.zlink","com.zjinnova.android.zlink.features.launcher.HiCarActivity")]:
            self.assertIn(f'"{action}" to Pair("{pkg}", "{activity}")',K)
            self.assertIn(pkg,[x.attrib.get("{http://schemas.android.com/apk/res/android}name") for x in M.findall("queries/package")])
        self.assertIn('if (action in setOf("carplay", "androidauto", "hicar")) return null',K)
        self.assertIn('exact ?: originalQf001Intent("zlink")',K)
        self.assertIn('Hardware 360°',K)
    def test_no_new_privileged_permission(self):
        names={x.attrib.get("{http://schemas.android.com/apk/res/android}name") for x in M.findall("uses-permission")}
        self.assertFalse(names & {"android.permission.WRITE_SECURE_SETTINGS","android.permission.INJECT_EVENTS","android.permission.READ_CONTACTS"})
if __name__=="__main__":unittest.main()
