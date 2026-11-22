"""Regression checks for user-approved DJ 88 BID screen touch layout.

Does not test OEM hardware or claim Themes integration.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")

class ApprovedLuxuryLayout(unittest.TestCase):
    def test_original_art_asset_is_preserved(self):
        self.assertIn("url('bid_approved.png')", HTML)

    def test_only_approved_primary_menu_labels(self):
        labels = re.findall(r'<button class="hit"[^>]*aria-label="([^"]+)"', HTML)
        self.assertEqual(labels, [
            "Acasă", "Radio", "Media YouTube", "Telefon", "Navigație",
            "Aplicații", "Mașină", "Setări", "Sunet", "CarPlay", "Android Auto"
        ])
        for forbidden in ("Netflix", "Spotify", "Play Store"):
            self.assertNotIn(forbidden, HTML)

    def test_youtube_is_media_shortcut(self):
        self.assertRegex(HTML, r'aria-label="Media YouTube"[^>]+onclick="launch\(\'youtube\'\)"')

    def test_never_fake_car_hardware(self):
        self.assertRegex(HTML, r'aria-label="CarPlay"[^>]+showUnsupported')
        self.assertRegex(HTML, r'aria-label="Android Auto"[^>]+showUnsupported')
        self.assertNotIn('id="clock"', HTML)

    def test_touch_areas_stay_inside_1280_by_720(self):
        for tag in re.findall(r'<button class="hit"[^>]+>', HTML):
            values = dict((key,int(value)) for key,value in
                          re.findall(r'(left|top|width|height):(\d+)px',tag))
            self.assertEqual(set(values), {"left","top","width","height"})
            self.assertGreater(values["width"],0)
            self.assertGreater(values["height"],0)
            self.assertLessEqual(values["left"]+values["width"],1280)
            self.assertLessEqual(values["top"]+values["height"],720)

if __name__ == "__main__":
    unittest.main()
