from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
P=(R/"app/src/main/java/ro/dj88bid/car/BidThemeProfiles.kt").read_text()
K=(R/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
A=(R/"app/src/main/java/ro/dj88bid/car/BidAppearance.kt").read_text()
H=(R/"app/src/main/java/ro/dj88bid/car/BidHomeEditor.kt").read_text()
class Themes(unittest.TestCase):
    def test_routes_and_isolation(self):
        self.assertIn('"bidthemeslots" -> themeProfiles.show()',K)
        self.assertIn("themeProfiles.handleResult(requestCode, resultCode, data)",K)
        self.assertIn("profiles.asset(",A);self.assertIn("profiles.asset(",H)
        self.assertIn('if(slot==0)activity.filesDir',P)
        self.assertIn('slot!=selected&&slot!=0',P)
    def test_import_allowlist_and_integrity(self):
        for s in ['seen.add(name)','!entry.isDirectory','name in names','require(total<=totalLimit','validateImage(name,out)','files.getString(name)==hash','stage.renameTo(destination)','palette in 0..3','manifest.json','SHA-256']:
            self.assertIn(s,P)
        for s in ['setprop','MANAGE_EXTERNAL_STORAGE','bid_car_art_','WRITE_SECURE_SETTINGS']:
            self.assertNotIn(s,P)
    def test_busy_and_fixed_geometry(self):
        self.assertIn('busy||editorsBusy()',P)
        self.assertIn('profiles.isBusy()',A);self.assertIn('profiles.isBusy()',H)
        self.assertIn('b.outWidth==1280&&b.outHeight==720',P)
        self.assertIn('Intent.ACTION_CREATE_DOCUMENT',P)
        self.assertIn('Intent.ACTION_OPEN_DOCUMENT',P)
if __name__=="__main__":unittest.main()
