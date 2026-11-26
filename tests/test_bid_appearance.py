from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
K=(R/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
A=(R/"app/src/main/java/ro/dj88bid/car/BidAppearance.kt").read_text()
class Appearance(unittest.TestCase):
    def test_route_and_default(self):
        for x in ['FunctionTile("Aspect BID","bidappearance",emptyList())','"bidappearance" -> bidAppearance.show()','bidAppearance.background(palette)','bidAppearance.icon(tile.key)','bidAppearance.handleResult(requestCode, resultCode, data)']:
            self.assertIn(x,K)
        self.assertIn('0xFF180B12.toInt(),0xFF4D192B.toInt(),0xFF110A10.toInt()',A)
        self.assertIn('prefs.getInt("palette",0)',A)
        self.assertIn('?: return base',A)
    def test_private_assets_and_restore(self):
        for x in ['Intent.ACTION_OPEN_DOCUMENT','requestBase = 560','AtomicFile(file(keys[i]))','target.failWrite(out)','16L*1024*1024','40000000L','keys.forEach { AtomicFile(file(it)).delete() }','if(i==0)1280 else 256']:
            self.assertIn(x,A)
        for x in ['setprop','MANAGE_EXTERNAL_STORAGE','bid_approved.png','com.st.carkit360camera','bid_car_art_']:
            self.assertNotIn(x,A)
    def test_only_non_safety_icons(self):
        keys=A.split('private val keys = arrayOf(',1)[1].split(')',1)[0]
        for x in ['reverse','camera360','canbus','steering','tpms']:
            self.assertNotIn(x,keys)
if __name__=="__main__":unittest.main()
