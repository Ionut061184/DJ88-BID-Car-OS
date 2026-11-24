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
        # Verify the FINAL CSS rule, not an obsolete declaration earlier in the file.
        status_rules = re.findall(r"#bidStatusLive\s*\{([^}]*)\}", self.css, re.S)
        self.assertTrue(status_rules)
        final = status_rules[-1]
        self.assertIn("left:808px;top:17px;width:340px;height:34px", final)
        self.assertIn("background:#090609", final)
        # The approved original weather/cloud icon occupies the reserved area to its left.
        self.assertGreaterEqual(int(re.search(r"left:(\d+)px", final).group(1)), 805)
        self.assertLessEqual(808 + 340, 1150)
        self.assertIn("background:#090609", self.css)
        self.assertIn("overflow:hidden;white-space:nowrap", self.css)

    def test_bluetooth_left_of_wireless_with_separate_icons(self):
        # User-approved order: WEATHER, BLUETOOTH, WI-FI, BATTERY, VOLTAGE.
        html_order = ["bidWeatherText", "bidBtText", "bidWifiText",
                      "bidBatteryText", "bidVoltageText"]
        positions = [self.html.index('id="' + key + '"') for key in html_order]
        self.assertEqual(positions, sorted(positions))
        # Native icons must be distinct rather than a duplicated 'BT' text.
        self.assertIn("var bluetoothIcon='<svg", self.js)
        self.assertIn("var wirelessIcon='<svg", self.js)
        self.assertIn("bt.innerHTML=bluetoothIcon", self.js)
        self.assertIn("wifi.innerHTML=wirelessIcon", self.js)
        self.assertIn("s.bluetooth===true", self.js)
        self.assertIn("s.wifi===true", self.js)
        self.assertNotIn("bt.textContent='BT?'", self.js)
        self.assertNotIn("wifi.textContent='WiFi?'", self.js)

    def test_gold_frame_clock_weather_and_functions_not_covered(self):
        self.assertIn("left:207px;top:16px;width:300px;height:36px", self.css)
        self.assertIn("left:236px;top:17px;width:77px;height:34px", self.css)
        self.assertIn("left:333px;top:18px;width:164px;height:32px", self.css)
        self.assertIn("background:transparent!important;border:0!important;box-shadow:none!important", self.css)
        self.assertIn("#functionsDock .dockIcon,#functionsDock > span{display:none!important}", self.css)

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
