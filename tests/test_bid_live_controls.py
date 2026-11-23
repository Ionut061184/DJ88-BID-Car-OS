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

    def test_weather_requires_real_network_data(self):
        self.assertIn("api.open-meteo.com", KOTLIN)
        self.assertIn("android.permission.INTERNET", MANIFEST)
        self.assertIn("updateWeather(", RUNTIME)
        self.assertIn("Vreme indisponibilă", RUNTIME)

    def test_no_fake_canbus_data(self):
        self.assertIn("#voltageLive,#mediaLive,#climateWarning", HTML)
        self.assertIn("#climateLeftLive,#climateRightLive,#mediaTimeLive{display:none!important}", HTML)
        self.assertIn("id=\"musicClean\"", HTML)
        self.assertIn("id=\"climateClean\"", HTML)
        self.assertNotIn('aria-label="Climatizare stânga"', HTML)
        self.assertIn("date CANBUS încă neverificate", RUNTIME)

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
