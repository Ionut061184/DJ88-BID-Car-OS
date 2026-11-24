"""Regression checks for the approved BID QF001 status bar.

These tests deliberately do not treat a missing/incorrect PNG as approved:
the separate SHA-256 CI gate checks the real binary.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app/src/main/assets"


class BidHeaderContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ASSETS / "index.html").read_text(encoding="utf-8")
        cls.css = (ASSETS / "bid_status.css").read_text(encoding="utf-8")
        cls.js = (ASSETS / "bid_status.js").read_text(encoding="utf-8")
        cls.runtime = (ASSETS / "bid_runtime.js").read_text(encoding="utf-8")
        cls.kotlin = (ROOT / "app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github/workflows/build-apk.yml").read_text(encoding="utf-8")

    def test_status_scripts_and_labels_present(self):
        self.assertIn('href="bid_status.css"', self.html)
        self.assertIn('src="bid_status.js"', self.html)
        for element in ("bidWeatherText", "bidBtText", "bidWifiText",
                        "bidBatteryText", "bidVoltageText", "clock", "dateLive"):
            self.assertIn('id="' + element + '"', self.html)

    def test_status_strictly_clipped_inside_black_header(self):
        self.assertRegex(self.css, r"#bidStatusLive\s*\{[^}]*overflow:hidden")
        self.assertIn("left:782px;top:15px;width:368px;height:36px", self.css)
        self.assertIn("background:#090609", self.css)
        self.assertIn("overflow:hidden;white-space:nowrap", self.css)

    def test_real_vehicle_voltage_preserved(self):
        self.assertIn("BID.vehicleVoltageSnapshot()", self.js)
        self.assertIn("vehicleVoltageSnapshot(): String = readQf001VehicleVoltage()", self.kotlin)
        self.assertIn("sys.qf.update_battery_power", self.kotlin)
        self.assertIn("v.available===true", self.js)
        self.assertIn("v.volts.toFixed(1)+' V'", self.js)
        self.assertNotIn("12.4 V", self.js)

    def test_real_weather_and_battery_only(self):
        self.assertIn("window.updateWeather=function", self.js)
        self.assertIn("BID.batterySnapshot()", self.js)
        self.assertIn("Number.isInteger(data.percent)", self.js)
        self.assertIn("BID.connectivitySnapshot()", self.js)

    def test_artwork_not_stretched_and_touch_geometry_scaled(self):
        self.assertIn("1280px;height:720px", self.html)
        self.assertIn("bid_approved.png", self.html)
        self.assertIn("100+0.84375*x", self.js)
        self.assertIn("0.84375*w", self.js)

    def test_ci_hash_guard_still_active(self):
        expected = "746b42fecf45cdb9216b06ee996f3520a33f9a9cefe9d816927db349f4800202"
        self.assertIn(expected, self.workflow)
        self.assertLess(self.workflow.index("Verify final approved BID artwork"),
                        self.workflow.index("Build debug APK"))
        self.assertIn('unzip -p "$file" assets/bid_approved.png', self.workflow)


if __name__ == "__main__":
    unittest.main()
