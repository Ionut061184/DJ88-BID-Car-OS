"""QF001 OEM Themes and dynamic launcher safety-contract regression tests.

These are STATIC checks only. Passing does not certify QF001 head-unit behavior,
firmware compatibility, OEM Themes enrollment, MCU/CANBUS, or an APK signature.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text(encoding="utf-8")
MANIFEST = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
GRADLE = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
HTML = (ROOT / "app/src/main/assets/index.html").read_text(encoding="utf-8")
RUNTIME = (ROOT / "app/src/main/assets/bid_runtime.js").read_text(encoding="utf-8")


class Qf001ThemesContract(unittest.TestCase):
    def test_lab_safe_never_registers_home(self):
        self.assertIn('applicationIdSuffix = ".labtest"', GRADLE)
        self.assertIn('manifestPlaceholders["bidHomeEnabled"] = "false"', GRADLE)
        self.assertIn('android:enabled="${bidHomeEnabled}"', MANIFEST)
        self.assertIn('android.intent.category.HOME', MANIFEST)

    def test_oem_candidate_separate_and_not_automatically_oem_theme(self):
        self.assertIn('applicationIdSuffix = ".qf001theme"', GRADLE)
        self.assertIn('manifestPlaceholders["bidHomeEnabled"] = "true"', GRADLE)
        self.assertIn("fun openQfThemes()", MAIN)
        self.assertIn("FactoryLauncherSelectActivity", MAIN)
        self.assertIn("resolved?.activityInfo?.exported == true", MAIN)
        self.assertIn("Nu modificăm firmware-ul", MAIN)

    def test_apps_list_uses_installed_launcher_activities(self):
        section = MAIN[MAIN.index("private fun showApps()"):]
        self.assertIn("packageManager.queryIntentActivities(", section)
        self.assertIn("Intent.CATEGORY_LAUNCHER", section)
        self.assertIn('getSharedPreferences("bid_app_grid_order"', section)
        self.assertIn("setOnLongClickListener", section)
        self.assertIn("startDragAndDrop", section)

    def test_uninstall_requires_android_dialog(self):
        section = MAIN[MAIN.index("private fun showApps()"):]
        self.assertIn("Intent(Intent.ACTION_DELETE", section)
        self.assertIn('Uri.parse("package:" + targetPkg)', section)
        self.assertIn("targetPkg != packageName", section)

    def test_oem_music_not_youtube_and_reversing_stays_oem(self):
        self.assertIn('"music" to Pair("com.qf.musicplayer"', MAIN)
        self.assertIn('originalQf001Intent(kind) ?: safeChoice', MAIN)
        self.assertIn("Camera marșarier este controlată automat de QF001", MAIN)
        self.assertIn('onclick="musicChoose(\'music\')"', HTML)
        self.assertIn('onclick="launch(\'youtube\')"', HTML)

    def test_main_ui_does_not_depend_on_privileged_theme_selection(self):
        self.assertIn('onclick="qfThemes()"', HTML)
        self.assertIn("function qfThemes()", RUNTIME)
        self.assertIn('url(\'bid_fullbleed.png\')', HTML)
        self.assertIn("file:///android_asset/index.html", MAIN)


if __name__ == "__main__":
    unittest.main()
