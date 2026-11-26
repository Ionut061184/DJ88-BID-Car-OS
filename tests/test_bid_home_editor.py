from pathlib import Path
import re
import unittest
R=Path(__file__).resolve().parents[1]
K=(R/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
A=(R/"app/src/main/java/ro/dj88bid/car/BidHomeEditor.kt").read_text()
HTML=(R/"app/src/main/assets/index.html").read_text()
class HomeEditor(unittest.TestCase):
    def test_route_and_private_resource(self):
        for s in ['"homeeditor" -> bidHomeEditor.show()','bidHomeEditor.handleResult(requestCode, resultCode, data)','applyHomeArtwork()','bidHomeEditor.serve(request.url, request.method)']:
            self.assertIn(s,K)
        for s in ['const val WIDTH = 1280','const val HEIGHT = 720','bounds.outWidth==WIDTH && bounds.outHeight==HEIGHT','AtomicFile(active)','target.failWrite(out)','setPositiveButton("Aplică")','active).delete()','Cache-Control','bid_fullbleed.png']:
            self.assertIn(s,A)
        self.assertNotIn('setprop',A)
    def test_preview_boxes_match_home_buttons(self):
        boxes={tuple(map(int,x)) for x in re.findall(r'Zone\("[^"]+",(\d+),(\d+),(\d+),(\d+)\)',A)}
        htmlboxes={tuple(map(int,x)) for x in re.findall(r'class="hit(?: topHit)?" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px',HTML)}
        self.assertEqual(boxes,htmlboxes)
if __name__=="__main__":unittest.main()
