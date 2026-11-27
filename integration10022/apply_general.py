from pathlib import Path
import sys
root=Path(sys.argv[1])
a=root/"app/src/main/assets"
k=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
def replace(s,old,new):
    assert s.count(old)==1, "Missing or ambiguous anchor: "+old[:100]
    return s.replace(old,new,1)
s=k.read_text()
s=replace(s,"    private fun enterFullscreen() {",'''    private fun enterFullscreen() {
        val prefs = getSharedPreferences("bid_general", MODE_PRIVATE)
        if (prefs.getBoolean("keep_awake", false)) window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        else window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if (prefs.getBoolean("system_bars", false)) {
            window.decorView.systemUiVisibility = 0
            return
        }''')
s=replace(s,"    inner class Bridge {",'''    inner class Bridge {
        @JavascriptInterface
        fun generalPreference(key: String): Boolean {
            if (webView.url != "file:///android_asset/index.html" || key !in listOf("keep_awake", "system_bars")) return false
            return getSharedPreferences("bid_general", MODE_PRIVATE).getBoolean(key,false)
        }

        @JavascriptInterface
        fun setGeneralPreference(key: String, enabled: Boolean) = runOnUiThread {
            if (webView.url == "file:///android_asset/index.html" && hasWindowFocus() && key in listOf("keep_awake", "system_bars")) {
                getSharedPreferences("bid_general", MODE_PRIVATE).edit().putBoolean(key,enabled).apply()
                enterFullscreen()
            }
        }

        @JavascriptInterface
        fun openVoiceAssistant() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus()) return@runOnUiThread
            try { startActivity(Intent(Intent.ACTION_VOICE_COMMAND)) }
            catch (_: android.content.ActivityNotFoundException) {
                android.widget.Toast.makeText(this@MainActivity,"Asistent vocal indisponibil",android.widget.Toast.LENGTH_SHORT).show()
            }
        }
''')
k.write_text(s)
p=a/"index.html"
s=p.read_text()
s=replace(s,'<button onclick="launch(\'original\')">Launcher original</button>','<button onclick="launch(\'original\')">Launcher original</button><button onclick="bidGeneralOpen()">Setări generale BID</button>')
s=replace(s,'</body></html>','<script src="bid_general.js"></script></body></html>')
p.write_text(s)
p=a/"bid_theme_builder.js"
s=p.read_text()
s=replace(s,"let snapEnabled=false,snapStep=10,reduceMotion=false;","let snapEnabled=false,snapStep=10,reduceMotion=false;")
# The existing precision checkbox is the single source of truth for theme animations.
s=replace(s,"const overlayIds=['drive'","const overlayIds=['bidGeneralModal','drive'")
p.write_text(s)
