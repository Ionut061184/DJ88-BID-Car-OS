package ro.dj88bid.car

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.view.KeyEvent
import android.media.AudioManager
import java.net.URL
import java.net.HttpURLConnection
import android.provider.Settings
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import org.json.JSONObject

class MainActivity : Activity() {
    private lateinit var webView: WebView

    @Suppress("DEPRECATION")
    private fun enterFullscreen() {
        window.decorView.systemUiVisibility =
            View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enterFullscreen()
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = false
        webView.settings.allowFileAccessFromFileURLs = false
        webView.settings.allowUniversalAccessFromFileURLs = false
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                if (request.url.scheme != "file") {
                    startSafely(Intent(Intent.ACTION_VIEW, request.url))
                    return true
                }
                return request.url.toString() != "file:///android_asset/index.html"
            }
        }
        webView.addJavascriptInterface(Bridge(), "BID")
        setContentView(webView)
        webView.loadUrl("file:///android_asset/index.html")
        webView.postDelayed({ refreshWeather() }, 1000)
    }

    // User-approved shortcuts only. Never invoke hidden OEM services or system intents.
    private val autoActions = linkedMapOf(
        "radio" to "Radio",
        "music" to "Muzică",
        "btcar" to "Bluetooth auto",
        "dsp" to "DSP"
    )

    // Identifiers extracted from the original ROCO K706 Android 10 firmware.
    // Presence in a manifest does NOT prove this third-party launcher can operate
    // the OEM hardware or that these activities are accessible on every device.
    private val knownQf001 = mapOf(
        "radio" to Pair("com.android.fmradio.ext", "com.android.fmradio.FmMainActivity"),
        "music" to Pair("com.qf.musicplayer", "com.qf.musicplayer.ui.MainActivity"),
        "btcar" to Pair("com.qf.bluetooth", "com.qf.bluetooth.BluetoothActivity"),
        "dsp" to Pair("com.qf.soundeffect", "com.qf.soundeffect.SoundActivity")
    )

    /**
     * Matches OEM package names extracted from the K706 firmware. Only launches
     * exported activities that Android exposes to a third-party application.
     * Never requests system UID, hidden binder services or hardware privileges.
     */
    private fun originalQf001Intent(action: String): Intent? {
        val component = knownQf001[action] ?: return null
        // Preferred: Android's published launcher entry (not a private component).
        val published = packageManager.getLaunchIntentForPackage(component.first)
        if (published != null &&
            published.resolveActivity(packageManager) != null) return published

        // Fallback: firmware-declared activity, only if the current OS exports it.
        val explicit = Intent(Intent.ACTION_MAIN)
            .setClassName(component.first, component.second)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        val resolved = packageManager.resolveActivity(explicit, 0)
        return if (resolved != null && resolved.activityInfo.exported) explicit else null
    }

    private fun assignedIntent(action: String): Intent? {
        val prefs = getSharedPreferences("bid_auto_shortcuts", MODE_PRIVATE)
        val pkg = prefs.getString(action + "_pkg", null) ?: return null
        val activity = prefs.getString(action + "_activity", null) ?: return null
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
            .setClassName(pkg, activity)
        return if (packageManager.resolveActivity(intent, 0) != null) intent else null
    }

    private fun chooseAutoApp(action: String) {
        val actionName = autoActions[action] ?: return
        val keywords = when (action) {
            "radio" -> listOf("radio", "fm", "tuner")
            "music" -> listOf("music", "muzic", "audio player", "player", "media")
            "btcar" -> listOf("bluetooth", "bt music", "bt phone", "handsfree", "hands-free", "car bt")
            "dsp" -> listOf("dsp", "equalizer", "equaliser", "sound effect", "audio settings")
            else -> emptyList()
        }
        val matches = packageManager.queryIntentActivities(
            Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
        ).filter { resolved ->
            val text = (resolved.loadLabel(packageManager).toString() + " " +
                resolved.activityInfo.packageName).lowercase(java.util.Locale.ROOT)
            resolved.activityInfo.packageName != packageName &&
                (keywords.any { keyword -> text.contains(keyword) } ||
                 resolved.activityInfo.packageName == knownQf001[action]?.first)
        }.distinctBy { it.activityInfo.packageName + "/" + it.activityInfo.name }
         .sortedWith(compareBy<android.content.pm.ResolveInfo>(
             { if (it.activityInfo.packageName == knownQf001[action]?.first) 0 else 1 },
             { it.loadLabel(packageManager).toString().lowercase(java.util.Locale.ROOT) }
         ))

        if (matches.isEmpty()) {
            android.app.AlertDialog.Builder(this)
                .setTitle("DJ 88 BID · " + actionName)
                .setMessage("Nu am găsit o aplicație lansabilă potrivită pentru " +
                    actionName + ". Pe Huawei este normal. Asocierea cu aplicația " +
                    "originală trebuie verificată pe K706; nu alegem aplicații la întâmplare.")
                .setPositiveButton("OK", null)
                .setNeutralButton("Șterge asocierea") { _, _ ->
                    getSharedPreferences("bid_auto_shortcuts", MODE_PRIVATE).edit()
                        .remove(action + "_pkg").remove(action + "_activity").apply()
                }.show()
            return
        }

        val names = arrayOf("Fără asociere (resetare)") +
            matches.map {
                (if (it.activityInfo.packageName == knownQf001[action]?.first)
                    "QF001 original · " else "") +
                    it.loadLabel(packageManager).toString() + " · " + it.activityInfo.packageName
            }
        android.app.AlertDialog.Builder(this)
            .setTitle("Asociază " + actionName + " · aplicații compatibile posibile")
            .setMessage("Aplicațiile QF001 apar primele dacă sunt instalate. Identificarea din firmware nu confirmă funcționarea hardware; alegerea este manuală.")
            .setItems(names) { _, position ->
                val prefs = getSharedPreferences("bid_auto_shortcuts", MODE_PRIVATE)
                if (position == 0) {
                    prefs.edit().remove(action + "_pkg").remove(action + "_activity").apply()
                    Toast.makeText(this, "Asocierea a fost anulată", Toast.LENGTH_SHORT).show()
                } else {
                    val app = matches[position - 1].activityInfo
                    prefs.edit().putString(action + "_pkg", app.packageName)
                        .putString(action + "_activity", app.name).apply()
                    Toast.makeText(this, "Asociere salvată: " + actionName, Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Renunță", null).show()
    }

    // Weather: user-selected city, no location tracking or API key.
    private val weatherCities = linkedMapOf(
        "Craiova" to Pair(44.3302, 23.7949),
        "Robăneștii de Sus" to Pair(44.316, 24.013),
        "București" to Pair(44.4268, 26.1025),
        "Iași" to Pair(47.1585, 27.6014)
    )
    private fun emitJs(script: String) {
        runOnUiThread { if (::webView.isInitialized) webView.evaluateJavascript(script, null) }
    }
    private fun refreshWeather() {
        val city = getSharedPreferences("bid_weather", MODE_PRIVATE).getString("city", "Craiova") ?: "Craiova"
        val coordinates = weatherCities[city] ?: weatherCities.getValue("Craiova")
        Thread {
            var connection: HttpURLConnection? = null
            try {
                val url = URL("https://api.open-meteo.com/v1/forecast?latitude=${coordinates.first}&longitude=${coordinates.second}&current=temperature_2m,weather_code&timezone=auto")
                connection = (url.openConnection() as HttpURLConnection).apply {
                    connectTimeout = 6000
                    readTimeout = 6000
                    requestMethod = "GET"
                }
                val raw = connection.inputStream.bufferedReader().use { it.readText() }
                val current = JSONObject(raw).getJSONObject("current")
                val value = current.getDouble("temperature_2m")
                val code = current.getInt("weather_code")
                val label = when (code) {
                    0 -> "Senin"
                    1,2,3 -> "Noros"
                    45,48 -> "Ceață"
                    in 51..67 -> "Ploaie"
                    in 71..77 -> "Ninsoare"
                    in 80..82 -> "Averse"
                    in 95..99 -> "Furtună"
                    else -> "Vreme"
                }
                emitJs("updateWeather(${JSONObject.quote(city)},${Math.round(value)},${JSONObject.quote(label)});")
            } catch (_: Exception) {
                emitJs("updateWeather(${JSONObject.quote(city)},null,'');")
            } finally {
                connection?.disconnect()
            }
        }.start()
    }

    inner class Bridge {
        @JavascriptInterface
        fun chooseWeatherCity() = runOnUiThread {
            val choices = weatherCities.keys.toTypedArray()
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Vreme BID · alege localitatea")
                .setItems(choices) { _, index ->
                    getSharedPreferences("bid_weather", MODE_PRIVATE).edit()
                        .putString("city", choices[index]).apply()
                    refreshWeather()
                }.setNegativeButton("Închide", null).show()
        }

        @JavascriptInterface
        fun mediaKey(action: String) = runOnUiThread {
            if (action == "open") {
                val intent = assignedIntent("music") ?: originalQf001Intent("music")
                if (intent != null) startSafely(intent) else chooseAutoApp("music")
                return@runOnUiThread
            }
            val code = when(action) {
                "previous" -> KeyEvent.KEYCODE_MEDIA_PREVIOUS
                "next" -> KeyEvent.KEYCODE_MEDIA_NEXT
                "playpause" -> KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
                else -> return@runOnUiThread
            }
            val audio = getSystemService(AUDIO_SERVICE) as AudioManager
            val uptime = android.os.SystemClock.uptimeMillis()
            audio.dispatchMediaKeyEvent(KeyEvent(uptime, uptime, KeyEvent.ACTION_DOWN, code, 0))
            audio.dispatchMediaKeyEvent(KeyEvent(uptime, uptime, KeyEvent.ACTION_UP, code, 0))
        }

        @JavascriptInterface
        fun diagnostics(): String {
            fun available(pkg: String): Boolean = try {
                @Suppress("DEPRECATION")
                packageManager.getPackageInfo(pkg, 0)
                true
            } catch (_: Exception) { false }
            return JSONObject().apply {
                put("mapsInstalled", available("com.google.android.apps.maps"))
                put("wazeInstalled", available("com.waze"))
                put("youtubeInstalled", available("com.google.android.youtube"))
                // Do not assume QF001 access based on a package being present.
                put("deviceManufacturer", android.os.Build.MANUFACTURER)
                put("deviceModel", android.os.Build.MODEL)
                put("androidRelease", android.os.Build.VERSION.RELEASE)
                put("originalSwoodGrainVisible", available("com.android.launcher.swood.grain"))
                val homeApps = packageManager.queryIntentActivities(
                    Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME), 0
                )
                val launchers = org.json.JSONArray()
                for (resolved in homeApps) {
                    val item = JSONObject()
                    item.put("label", resolved.loadLabel(packageManager).toString())
                    item.put("package", resolved.activityInfo.packageName)
                    launchers.put(item)
                }
                put("availableHomeLaunchers", launchers)
                val carApps = org.json.JSONArray()
                val labels = packageManager.queryIntentActivities(
                    Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
                )
                for (resolved in labels) {
                    val name = resolved.loadLabel(packageManager).toString()
                    val id = resolved.activityInfo.packageName
                    val lookup = (name + " " + id).lowercase(java.util.Locale.ROOT)
                    val keywords = listOf("radio", "bluetooth", "bt music", "bts", "dsp", "equalizer", "eq", "car settings", "music", "muzic", "vehicle")
                    if (keywords.any { lookup.contains(it) }) {
                        val info = JSONObject()
                        info.put("label", name)
                        info.put("package", id)
                        info.put("activity", resolved.activityInfo.name)
                        info.put("verifiedQf001Function", false)
                        carApps.put(info)
                    }
                }
                put("candidateCarApps", carApps)
                val shortcuts = JSONObject()
                val prefs = getSharedPreferences("bid_auto_shortcuts", MODE_PRIVATE)
                for ((key, label) in autoActions) {
                    val info = JSONObject()
                    info.put("label", label)
                    info.put("package", prefs.getString(key + "_pkg", null) ?: if (originalQf001Intent(key) != null) "QF001 detectat automat" else "neconfigurat")
                    info.put("available", assignedIntent(key) != null || originalQf001Intent(key) != null)
                    shortcuts.put(key, info)
                }
                put("assignedAutoShortcuts", shortcuts)
                val known = JSONObject()
                for ((action, component) in knownQf001) {
                    val matches = packageManager.queryIntentActivities(
                        Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
                    )
                    val identified = matches.any {
                        it.activityInfo.packageName == component.first &&
                        it.activityInfo.name == component.second
                    }
                    known.put(action, JSONObject().apply {
                        put("package", component.first)
                        put("activity", component.second)
                        put("launchableVisible", identified)
                    })
                }
                put("originalQf001Apps", known)
                put("qf001SystemIntegrationTested", false)
                val vehiclePackage = "com.qf.vehicle"
                put("canbusPackage", vehiclePackage)
                put("canbusPackageVisible", available(vehiclePackage))
                val vehicleLaunch = packageManager.getLaunchIntentForPackage(vehiclePackage)
                put("canbusHasPublicLauncher", vehicleLaunch != null)
                put("canbusDataBridgeVerified", false)
                put("climatronicLiveAvailable", false)
                put("carBatteryVoltageAvailable", false)
            }.toString()
        }

        // Presents detected apps to the user; never invokes privileged QF001 actions.
        @JavascriptInterface
        fun configureAuto(action: String) = runOnUiThread {
            if (autoActions.containsKey(action)) chooseAutoApp(action)
        }

        @JavascriptInterface
        fun launchAuto(action: String) = runOnUiThread {
            if (!autoActions.containsKey(action)) return@runOnUiThread
            val userSelected = assignedIntent(action)
            // User's explicit selection takes precedence, otherwise use the actual
            // installed OEM QF001 package when it is publicly launchable.
            val intent = userSelected ?: originalQf001Intent(action)
            if (intent != null) {
                try { startActivity(intent) }
                catch (_: Exception) {
                    Toast.makeText(this@MainActivity,
                        "Aplicația originală nu permite lansarea. Selectează alta.",
                        Toast.LENGTH_LONG).show()
                    chooseAutoApp(action)
                }
            } else {
                Toast.makeText(this@MainActivity,
                    "Nu există o aplicație OEM accesibilă pentru " + autoActions[action],
                    Toast.LENGTH_LONG).show()
                chooseAutoApp(action)
            }
        }

        @JavascriptInterface
        fun showCarApps() = runOnUiThread {
            val candidates = packageManager.queryIntentActivities(
                Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
            ).filter {
                val search = (it.loadLabel(packageManager).toString() + " " +
                    it.activityInfo.packageName).lowercase(java.util.Locale.ROOT)
                listOf("radio", "bluetooth", "bt music", "dsp", "equalizer", "car settings", "music", "muzic").any { key ->
                    search.contains(key)
                }
            }.sortedBy { it.loadLabel(packageManager).toString() }
            if (candidates.isEmpty()) {
                Toast.makeText(this@MainActivity, "Nu sunt detectate aplicații auto lansabile", Toast.LENGTH_LONG).show()
                return@runOnUiThread
            }
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("DJ 88 BID · Aplicații auto detectate (netestate)")
                .setItems(candidates.map { it.loadLabel(packageManager).toString() }.toTypedArray()) { _, pos ->
                    val a = candidates[pos].activityInfo
                    startSafely(Intent(Intent.ACTION_MAIN).apply {
                        addCategory(Intent.CATEGORY_LAUNCHER)
                        setClassName(a.packageName, a.name)
                    })
                }
                .setNegativeButton("Renunță", null).show()
        }

        @JavascriptInterface
        fun openQfThemes() = runOnUiThread {
            // OEM implementation identified in QF_CarSettings.apk from K706 firmware.
            // Can open only if this particular device exports it to third-party apps.
            val pkgs = listOf("com.qf.carsettings", "com.qf.carsetting")
            val classes = listOf(
                "com.qf.carsettings.activity.FactoryLauncherSelectActivity",
                "com.qf.carsetting.activity.FactoryLauncherSelectActivity")
            for (pkg in pkgs) {
                for (cls in classes) {
                    val intent = Intent(Intent.ACTION_MAIN)
                        .setClassName(pkg, cls)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    val resolved = packageManager.resolveActivity(intent, 0)
                    if (resolved?.activityInfo?.exported == true) {
                        try {
                            startActivity(intent)
                            return@runOnUiThread
                        } catch (_: Exception) { /* Try next exported component. */ }
                    }
                }
            }
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("QF001 · Themes original")
                .setMessage("Selectorul OEM nu este expus pentru această aplicație ori nu este instalat. " +
                    "Nu modificăm firmware-ul și nu încercăm să ocolim protecțiile OEM. " +
                    "Deschide Themes din Setările originale QF001.")
                .setPositiveButton("Deschide setările QF001") { _, _ ->
                    for (pkg in pkgs) {
                        val intent = packageManager.getLaunchIntentForPackage(pkg)
                        if (intent != null) {
                            startSafely(intent)
                            return@setPositiveButton
                        }
                    }
                    startSafely(Intent(Settings.ACTION_SETTINGS))
                }
                .setNegativeButton("Închide", null)
                .show()
        }

        @JavascriptInterface
        fun open(command: String) = runOnUiThread {
            when (command) {
                "maps" -> openPreferred("com.google.android.apps.maps", "geo:0,0", "https://www.google.com/maps")
                "waze" -> openPreferred("com.waze", "waze://", "https://waze.com/ul")
                "youtube" -> openPreferred("com.google.android.youtube", "https://www.youtube.com", "https://www.youtube.com")
                "phone" -> {
                    // K706 uses the OEM Bluetooth hands-free app for calls;
                    // a SIM / Android dialer is not required.
                    val handsFree = assignedIntent("btcar") ?: originalQf001Intent("btcar")
                    if (handsFree != null) {
                        try { startActivity(handsFree) }
                        catch (_: Exception) {
                            Toast.makeText(this@MainActivity,
                                "Bluetooth auto nu a pornit; selectează aplicația pentru apeluri.",
                                Toast.LENGTH_LONG).show()
                            chooseAutoApp("btcar")
                        }
                    } else {
                        Toast.makeText(this@MainActivity,
                            "Asociază aplicația Bluetooth auto pentru apeluri.",
                            Toast.LENGTH_LONG).show()
                        chooseAutoApp("btcar")
                    }
                }
                "bluetooth" -> startSafely(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                "settings" -> startSafely(Intent(Settings.ACTION_SETTINGS))
                "apps" -> showApps()
                "canbus" -> {
                    val diagnostic = "com.qf.vehicle"
                    val app = packageManager.getLaunchIntentForPackage(diagnostic)
                    if (app != null) {
                        startSafely(app)
                    } else {
                        android.app.AlertDialog.Builder(this@MainActivity)
                            .setTitle("BID · CANBUS QF001")
                            .setMessage("Aplicația OEM CANBUS nu expune o activitate publică de lansare. Nu încercăm să accesăm servicii interne sau să modificăm configurația MCU. Deschide Setări auto originale pentru verificare.")
                            .setPositiveButton("Setări auto") { _, _ ->
                                val settings = packageManager.getLaunchIntentForPackage("com.qf.carsettings")
                                    ?: packageManager.getLaunchIntentForPackage("com.qf.carsetting")
                                if (settings != null) startSafely(settings)
                                else startSafely(Intent(Settings.ACTION_SETTINGS))
                            }.setNegativeButton("Închide", null).show()
                    }
                }
                "car" -> {
                    val original = packageManager.getLaunchIntentForPackage("com.qf.carsettings")
                        ?: packageManager.getLaunchIntentForPackage("com.qf.carsetting")
                    if (original != null) startSafely(original) else startSafely(Intent(Settings.ACTION_SETTINGS))
                }
                "carplay" -> findCompanion(listOf("zlink", "tlink", "carlink", "carplay", "autokit"), "CarPlay")
                "androidauto" -> findCompanion(listOf("zlink", "tlink", "carlink", "android auto", "autokit"), "Android Auto")
                "wifi" -> startSafely(Intent(Settings.ACTION_WIFI_SETTINGS))
                "dateSettings" -> startSafely(Intent(Settings.ACTION_DATE_SETTINGS))
                "original" -> startSafely(Intent(Settings.ACTION_HOME_SETTINGS))
                else -> Toast.makeText(this@MainActivity, "Comandă necunoscută", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun findCompanion(keywords: List<String>, title: String) {
        val candidates = packageManager.queryIntentActivities(
            Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
        ).filter { resolved ->
            val description = (resolved.loadLabel(packageManager).toString() + " " +
                resolved.activityInfo.packageName).lowercase(java.util.Locale.ROOT)
            keywords.any { key -> description.contains(key) }
        }
        if (candidates.isEmpty()) {
            Toast.makeText(this, title + ": nu există o aplicație compatibilă instalată", Toast.LENGTH_LONG).show()
            return
        }
        android.app.AlertDialog.Builder(this).setTitle(title + " · aplicații disponibile")
            .setItems(candidates.map { it.loadLabel(packageManager).toString() }.toTypedArray()) { _, i ->
                val app = candidates[i].activityInfo
                startSafely(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
                    .setClassName(app.packageName, app.name))
            }.setNegativeButton("Renunță", null).show()
    }
    private fun openPreferred(pkg: String, link: String, fallback: String) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(link)).apply { setPackage(pkg) }
        try { startActivity(intent) }
        catch (_: Exception) { startSafely(Intent(Intent.ACTION_VIEW, Uri.parse(fallback))) }
    }

    private fun startSafely(intent: Intent) {
        try { startActivity(intent) }
        catch (_: Exception) {
            Toast.makeText(this, "Aplicația nu este disponibilă", Toast.LENGTH_SHORT).show()
        }
    }

    private fun showApps() {
        val apps = packageManager.queryIntentActivities(
            Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
        ).filter { it.activityInfo.packageName != packageName }
         .sortedBy { it.loadLabel(packageManager).toString().lowercase() }
        val names = apps.map { it.loadLabel(packageManager).toString() }.toTypedArray()
        if (names.isEmpty()) {
            startSafely(Intent(Settings.ACTION_APPLICATION_SETTINGS))
            return
        }
        android.app.AlertDialog.Builder(this)
            .setTitle("DJ 88 BID · Aplicații")
            .setItems(names) { _, which ->
                val a = apps[which].activityInfo
                val intent = Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_LAUNCHER)
                    setClassName(a.packageName, a.name)
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                startSafely(intent)
            }
            .setNegativeButton("Închide", null).show()
    }

    @Suppress("DEPRECATION")
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) enterFullscreen()
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        webView.evaluateJavascript("closeAll();", null)
    }
}
