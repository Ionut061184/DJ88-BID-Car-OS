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
        self.assertIn("left:837px;top:17px;width:414px;height:34px", final)
        self.assertIn("background:#090609", final)
        # The approved original weather/cloud icon occupies the reserved area to its left.
        self.assertEqual(int(re.search(r"left:(\d+)px", final).group(1)), 837)
        self.assertLessEqual(837 + 414, 1280)
        self.assertIn("background:#090609", self.css)
        self.assertIn("overflow:hidden;white-space:nowrap", self.css)


    def test_approved_phone_banner_positions_are_last_effective_rules(self):
        # Latest labSafe on-phone adjustment; no changes to original PNG.
        def final_rule(selector):
            import re
            matches = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", self.css, re.S)
            self.assertTrue(matches)
            return matches[-1]
        self.assertIn("left:140px;top:16px;width:345px;height:36px", final_rule("#stage:after"))
        self.assertIn("left:160px;top:17px;width:125px;height:34px", final_rule("#clock"))
        self.assertIn("left:345px;top:18px;width:132px;height:32px", final_rule("#dateLive"))
        self.assertIn("left:837px;top:17px;width:414px;height:34px", final_rule("#bidStatusLive"))

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

    def test_music_uses_qf001_player_not_youtube(self):
        self.assertIn('"music" to Pair("com.qf.musicplayer",', self.kotlin)
        self.assertIn('originalQf001Intent(kind) ?: safeChoice', self.kotlin)
        self.assertIn('!text.contains("youtube")', self.kotlin)
        self.assertIn('"music" -> listOf("qf.musicplayer",', self.kotlin)
        # Keep the separate approved YouTube button.
        self.assertIn('aria-label="YouTube" onclick="launch(\'youtube\')"', self.html)
        # The visible left-side Muzică tile is NOT the separate YouTube tile.
        self.assertIn('aria-label="Muzică: player audio original QF001" onclick="musicChoose(\'music\')"', self.html)
        self.assertNotIn('aria-label="Media YouTube" onclick="launch(\'youtube\')"', self.html)
        self.assertIn("if(window.BID && typeof BID.openMediaOem==='function'){BID.openMediaOem(kind)}", self.runtime)

    def test_bluetooth_wifi_icons_match_touch_zones(self):
        self.assertIn('#bidStatusLive .bidWeather{flex:0 0 125px', self.css)
        self.assertIn('#bidStatusLive .bidConnection{flex:0 0 auto;gap:18px}', self.css)
        self.assertIn('#bidStatusLive .bidBattery{margin-left:auto}', self.css)
        self.assertIn('aria-label="Bluetooth: deschide setările"', self.html)
        self.assertIn('aria-label="Wi-Fi: deschide setările"', self.html)

    def test_real_fullbleed_art_and_identical_touch_mapping(self):
        self.assertIn("url('bid_fullbleed.png')", self.html)
        generator = (ROOT / "scripts/build_bid_fullbleed.py").read_text(encoding="utf-8")
        self.assertIn("src.crop((300, 0, 1000, 720))", generator)
        self.assertIn("out.crop((300, 0, 1000, 720))", generator)
        self.assertIn("if(x<255)return x-100", self.js)
        self.assertIn("if(x<300)return 155+(x-255)*145/45", self.js)
        self.assertIn("if(x<=1000)return x", self.js)
        self.assertIn("if(x<1035)return 1000+(x-1000)*135/35", self.js)
        self.assertIn("return x+100", self.js)
        self.assertIn("button.style.left=dstStart+'px'", self.js)
        self.assertIn("button.style.width=Math.max(1,dstEnd-dstStart)+'px'", self.js)
        self.assertIn("#stage::before{display:none!important}", self.css)
        self.assertIn("python3 scripts/build_bid_fullbleed.py", self.workflow)

    def test_full_width_side_extension_preserves_approved_image_and_touches(self):
        self.assertIn("#stage::before{", self.css)
        self.assertIn("0 0/100px 100% no-repeat", self.css)
        self.assertIn("1180px 0/100px 100% no-repeat", self.css)
        self.assertIn("pointer-events:none", self.css)
        self.assertIn("100+0.84375*x", self.js)
        self.assertIn("bid_approved.png", self.html)

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
        self.assertIn("0.84375*(x+w)", self.js)

    def test_ci_hash_guard_still_active(self):
        expected = "746b42fecf45cdb9216b06ee996f3520a33f9a9cefe9d816927db349f4800202"
        self.assertIn(expected, self.workflow)
        self.assertLess(self.workflow.index("Verify final approved BID artwork"),
                        self.workflow.index("Build debug APK"))
        self.assertIn('unzip -p "$file" assets/bid_approved.png', self.workflow)


if __name__ == "__main__":
    unittest.main()
