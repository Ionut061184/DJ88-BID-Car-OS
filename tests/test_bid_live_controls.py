"""Source-level contract tests for BID real-data safety and 1280x720 touchscreen."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
RUNTIME = (ROOT / "app/src/main/assets/bid_runtime.js").read_text(encoding="utf-8")
KOTLIN = (ROOT / "app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text(encoding="utf-8")
MANIFEST = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")


class TestBidLiveControls(unittest.TestCase):
    def test_clock_and_date_are_device_driven(self):
        self.assertIn('src="bid_runtime.js"', HTML)
        self.assertIn("new Date()", RUNTIME)
        self.assertIn("dateLive", HTML)
        self.assertIn("tick();setInterval(tick,10000)", RUNTIME)

    def test_phone_layout_no_black_bars_and_no_duplicate_clock(self):
        self.assertIn("body:before", HTML)
        self.assertIn("filter:blur(36px)", HTML)
        self.assertIn("#clock{left:132px", HTML)
        self.assertIn("#dateLive{left:278px", HTML)
        self.assertIn("Math.min(innerWidth/1280,innerHeight/720)", RUNTIME)

    def test_top_status_controls_have_nonoverlapping_hit_zones(self):
        import re
        hits = re.findall(r'<button class="hit topHit" style="left:(\\d+)px;top:13px;width:(\\d+)px;height:62px"', HTML)
        # Weather, Bluetooth, Wi-Fi, connectivity, battery: no horizontal overlaps
        self.assertEqual(len(hits), 5)
        pairs = [(int(x), int(w)) for x, w in hits]
        for (left, width), (next_left, _) in zip(pairs, pairs[1:]):
            self.assertLessEqual(left + width, next_left)
        self.assertIn('onclick="configureWeather()"', HTML)
        self.assertIn('onclick="goHome()"', HTML)
        self.assertIn('onclick="batteryDetails()"', HTML)
        self.assertIn('function goHome(){', RUNTIME)
        self.assertIn('function batteryDetails(){', RUNTIME)
        self.assertIn('#clock,#dateLive,#batteryAndroidLive,#voltageLive{pointer-events:none}', HTML)

    def test_weather_requires_real_network_data(self):
        self.assertIn("api.open-meteo.com", KOTLIN)
        self.assertIn("android.permission.INTERNET", MANIFEST)
        self.assertIn("updateWeather(", RUNTIME)
        self.assertIn("Vreme indisponibilă", RUNTIME)

    def test_no_fake_canbus_data(self):
        # Keep approved artwork fully visible, including the app dock.
        self.assertIn("#musicClean,#climateClean{display:none!important}", HTML)
        self.assertNotIn('id="musicClean"', HTML)
        self.assertNotIn('id="climateClean"', HTML)
        # Android battery != vehicle CANBUS voltage.
        self.assertIn('id="batteryAndroidLive"', HTML)
        self.assertIn('id="voltageLive"', HTML)
        self.assertIn("realVolts===null?'— V':realVolts.toFixed(1)+' V'", RUNTIME)
        self.assertIn("sys.qf.update_battery_power", KOTLIN)
        self.assertIn("decivolts / 10.0", KOTLIN)
        self.assertIn("decivolts !in 90..165", KOTLIN)
        self.assertIn("fun vehicleVoltageSnapshot(): String", KOTLIN)
        self.assertNotIn("Runtime.getRuntime().exec(\"su\"", KOTLIN)
        self.assertIn("vehicleVoltageAvailable", KOTLIN)
        self.assertNotIn('aria-label="Climatizare stânga"', HTML)
        self.assertIn("date CANBUS încă neverificate", RUNTIME)

    def test_bottom_music_menu_has_discovered_qf001_categories(self):
        self.assertIn('onclick="openMusicMenu()"', HTML)
        self.assertIn('id="functionsDock"', HTML)
        self.assertIn('<span>Funcții</span>', HTML)
        self.assertIn('class="dockIcon"', HTML)
        self.assertNotIn('onclick="openMusicMenu()">Muzică</button>', HTML)
        self.assertIn("id=\"musicChoices\"", HTML)
        for category in ("Multimedia", "Mașină", "Navigație și utilitare"):
            self.assertIn("<h3>" + category + "</h3>", HTML)
        for shortcut in ("tpms", "steering", "gps", "files", "gallery",
                         "video", "weather", "manual", "music", "radio", "dsp"):
            self.assertIn("musicChoose('" + shortcut + "')", HTML)
        self.assertIn("fun openMediaOem(kind: String)", KOTLIN)
        self.assertIn("Camera marșarier funcționează automat", RUNTIME)

    def test_media_transport_and_companion_icons(self):
        self.assertNotIn("mediaKey('previous')", HTML)
        self.assertNotIn("mediaKey('playpause')", HTML)
        self.assertNotIn("mediaKey('next')", HTML)
        self.assertNotIn('aria-label="Muzică"', HTML)
        self.assertIn("dispatchMediaKeyEvent", KOTLIN)
        for action in ('"car"', '"carplay"', '"androidauto"', '"wifi"'):
            self.assertIn(action, KOTLIN)

    def test_bid_crest_opens_original_luxury_menu(self):
        self.assertIn('aria-label="BID Bespoke Design – deschide meniul Luxury"', HTML)
        self.assertIn('onclick="luxury(true)"', HTML)
        for command in ("luxuryLaunch('maps')", "luxuryLaunch('phone')",
                        "luxuryAuto('radio')",
                        "luxuryAuto('btcar')", "luxuryAuto('dsp')",
                        "theme(true)", "driving()"):
            self.assertIn(command, HTML)

    def test_safe_original_launcher_access(self):
        self.assertIn('applicationIdSuffix = ".labtest"', (ROOT / "app/build.gradle.kts").read_text())
        self.assertIn('bidHomeEnabled', MANIFEST)


if __name__ == "__main__":
    unittest.main()
