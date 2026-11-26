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
        boxes={tuple(map(int,x)) for x in re.findall(r'Zone\("[^"]+",(\d+),(\d+),(\d+),(\d+)\)',A.split("private val zones = listOf(",1)[1].split("private val patches",1)[0])}
        htmlboxes={tuple(map(int,x)) for x in re.findall(r'class="hit(?: topHit)?" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px',HTML)}
        self.assertEqual(len(htmlboxes),23)
        self.assertEqual(len(boxes),23)
        self.assertEqual(boxes,htmlboxes)
    def test_patch_regions_and_clipping(self):
        region=A.split("private val patches = listOf(",1)[1].split("private fun choosePatch",1)[0]
        rects=[tuple(map(int,x)) for x in re.findall(r'Zone\("[^"]+",(\d+),(\d+),(\d+),(\d+)\)',region)]
        self.assertEqual(len(rects),9)
        touch=[tuple(map(int,x)) for x in re.findall(r'class="hit(?: topHit)?" style="left:(\d+)px;top:(\d+)px;width:(\d+)px;height:(\d+)px',HTML)]
        def overlap(a,b):
            x,y,w,h=a;X,Y,W,H=b
            return x<X+W and X<x+w and y<Y+H and Y<y+h
        for i,(x,y,w,h) in enumerate(rects):
            self.assertTrue(0<=x<x+w<=1280 and 0<=y<y+h<=720)
            hits=[r for r in touch if overlap((x,y,w,h),r)]
            if i==0:self.assertEqual(hits,[])
            else:
                self.assertEqual(len(hits),1)
                X,Y,W,H=hits[0]
                self.assertTrue(X<=x and Y<=y and x+w<=X+W and y+h<=Y+H)
        for x in ["PATCH_BASE = 590","c.clipRect(","preview(merged,true)","zoom=it.coerceAtLeast(10)","Bitmap.createBitmap(WIDTH,HEIGHT"]:
            self.assertIn(x,A)
if __name__=="__main__":unittest.main()
