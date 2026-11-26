from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
K=(ROOT/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
A=(ROOT/"app/src/main/java/ro/dj88bid/car/BidCarArtwork.kt").read_text()
class Artwork(unittest.TestCase):
    def test_route_and_result(self):
        self.assertIn('FunctionTile("Model DJ 88 BID","carart",emptyList())',K)
        self.assertIn('"carart" -> carArtwork.show()',K)
        self.assertIn('carArtwork.handleResult(requestCode, resultCode, data)',K)
    def test_safe_private_import(self):
        for value in ['Intent.ACTION_OPEN_DOCUMENT','uri.scheme != "content"','16L * 1024 * 1024','40000000L','AtomicFile(file(slot))','target.failWrite(out)','staging.inputStream().use { it.copyTo(out) }']:
            self.assertIn(value,A)
        self.assertNotIn('setprop',A)
        self.assertNotIn('com.st.carkit360camera',A)
    def test_export_reference_package(self):
        for value in ['Intent.ACTION_CREATE_DOCUMENT','application/zip','ZipOutputStream','MessageDigest.getInstance("SHA-256")','ZipEntry("manifest.json")','put("nativeBirdviewModel", false)','openOutputStream(uri, "w")','slotIds[i]']:
            self.assertIn(value,A)
        self.assertNotIn('MANAGE_EXTERNAL_STORAGE',A)
    def test_zlink_regression(self):
        self.assertIn('val exact = originalQf001Intent(command)',K)
        self.assertNotIn('val exact = originalQf001Intent(action)',K)
if __name__=="__main__":unittest.main()
