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
    private lateinit var bidThemeImage: BidThemeImage
    private lateinit var mapWidget: BidMapWidget
    private lateinit var gpsWeather: BidGpsWeather
    private lateinit var bidGpsSpeed: BidGpsSpeed
    private lateinit var bidDriveContext: BidDriveContext
    private var speedForeground = false
    private lateinit var adaptiveDisplay: BidAdaptiveDisplay
    private var permissionRequestInProgress = false
    private var pageReady = false
    private fun permissionGranted(permission: String): Boolean =
        checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
    private fun hasLocation(): Boolean =
        permissionGranted(android.Manifest.permission.ACCESS_FINE_LOCATION) ||
        permissionGranted(android.Manifest.permission.ACCESS_COARSE_LOCATION)
    private fun askGpsOnce(explicit: Boolean = false) {
        if (permissionRequestInProgress || hasLocation()) return
        val prefs = getSharedPreferences("bid_permission_choices", MODE_PRIVATE)
        if (!explicit && prefs.getBoolean("gpsAsked", false)) return
        prefs.edit().putBoolean("gpsAsked", true).apply()
        permissionRequestInProgress = true
        requestPermissions(arrayOf(android.Manifest.permission.ACCESS_FINE_LOCATION,
            android.Manifest.permission.ACCESS_COARSE_LOCATION), 417)
    }

    // One initial setup, only permissions missing on this device.
    private fun configureIndicatorsOnce() {
        if (permissionRequestInProgress) return
        val prefs = getSharedPreferences("bid_permission_choices", MODE_PRIVATE)
        if (prefs.getBoolean("initialIndicatorsAskedV6", false)) return
        val needed = mutableListOf<String>()
        if (autoWeather() && !hasLocation()) {
            needed.add(android.Manifest.permission.ACCESS_FINE_LOCATION)
            needed.add(android.Manifest.permission.ACCESS_COARSE_LOCATION)
        }
        prefs.edit().putBoolean("initialIndicatorsAskedV6", true)
            .putBoolean("gpsAsked", true).apply()
        if (needed.isEmpty()) return
        permissionRequestInProgress = true
        requestPermissions(needed.toTypedArray(), 419)
    }

    private fun openIndicatorPermissions() {
        val items = mutableListOf<Pair<String, String>>()
        if (android.os.Build.VERSION.SDK_INT >= 31 &&
            packageManager.hasSystemFeature("android.hardware.bluetooth") &&
            !permissionGranted("android.permission.BLUETOOTH_CONNECT"))
            items.add("Bluetooth · permite verificarea conexiunii" to "android.permission.BLUETOOTH_CONNECT")
        if (!hasLocation()) items.add("Vreme GPS · permite locația" to "GPS")
        val builder = android.app.AlertDialog.Builder(this)
            .setTitle("BID · Permisiuni opționale")
            .setNegativeButton("Închide", null)
            .setNeutralButton("Setări Android") { _, _ ->
                startSafely(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + packageName)))
            }
        if (items.isEmpty()) builder.setMessage("Permisiunile necesare sunt deja acordate sau nu sunt disponibile pe acest dispozitiv.")
        else builder.setItems(items.map { it.first }.toTypedArray()) { _, pos ->
            val permission = items[pos].second
            if (permission == "GPS") askGpsOnce(true)
            else if (!permissionRequestInProgress && !permissionGranted(permission)) {
                permissionRequestInProgress = true
                requestPermissions(arrayOf(permission), 418)
            }
        }
        builder.show()
    }
    private fun autoWeather(): Boolean =
        getSharedPreferences("bid_weather", MODE_PRIVATE).getBoolean("gps", true)

    override fun onResume() {
        super.onResume()
        if (::mapWidget.isInitialized) mapWidget.start()
        speedForeground = true
        if (pageReady && ::bidGpsSpeed.isInitialized) bidGpsSpeed.start()
        if (::adaptiveDisplay.isInitialized) adaptiveDisplay.start()
        if (pageReady && ::gpsWeather.isInitialized && autoWeather()) refreshWeather()
    }

    override fun onPause() {
        if (::mapWidget.isInitialized) mapWidget.stop()
        speedForeground = false
        if (::bidGpsSpeed.isInitialized) bidGpsSpeed.stop()
        if (::gpsWeather.isInitialized) gpsWeather.stop()
        if (::adaptiveDisplay.isInitialized) adaptiveDisplay.stop()
        super.onPause()
    }

    override fun onDestroy() {
        if (::bidThemeImage.isInitialized) bidThemeImage.close()
        if (::bidDriveContext.isInitialized) {
            if (::webView.isInitialized) webView.removeJavascriptInterface("BIDDrive")
            bidDriveContext.close()
        }
        if (::bidGpsSpeed.isInitialized) bidGpsSpeed.stop()
        if (::gpsWeather.isInitialized) gpsWeather.close()
        super.onDestroy()
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode,resultCode,data)
        if (::bidThemeImage.isInitialized && bidThemeImage.result(requestCode,resultCode,data)) return
        if (::mapWidget.isInitialized) mapWidget.result(requestCode,resultCode)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 417 || requestCode == 418 || requestCode == 419) {
            permissionRequestInProgress = false
            if (autoWeather() && ::gpsWeather.isInitialized) gpsWeather.start()
            if (speedForeground && pageReady && ::bidGpsSpeed.isInitialized) bidGpsSpeed.start()
        }
    }

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
            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (url == "file:///android_asset/index.html") {
                    pageReady = true
                    if (speedForeground && ::bidGpsSpeed.isInitialized) bidGpsSpeed.start()
                    configureIndicatorsOnce()
                    refreshWeather()
                }
            }
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                if (request.url.scheme != "file") {
                    startSafely(Intent(Intent.ACTION_VIEW, request.url))
                    return true
                }
                return request.url.toString() != "file:///android_asset/index.html"
            }
        }
        webView.addJavascriptInterface(Bridge(), "BID")
        val root = android.widget.FrameLayout(this)
        root.addView(webView, android.widget.FrameLayout.LayoutParams(-1,-1))
        setContentView(root)
        mapWidget = BidMapWidget(this,root,webView)
        webView.addJavascriptInterface(mapWidget,"BIDWidget")
        bidThemeImage = BidThemeImage(this,webView)
        webView.addJavascriptInterface(bidThemeImage,"BIDThemeImage")
        gpsWeather = BidGpsWeather(this, ::emitJs)
        bidDriveContext = BidDriveContext(this, webView)
        webView.addJavascriptInterface(bidDriveContext, "BIDDrive")
        bidGpsSpeed = BidGpsSpeed(this, webView, bidDriveContext)
        adaptiveDisplay = BidAdaptiveDisplay(this)
        webView.loadUrl("file:///android_asset/index.html")

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
            // Avoid generic "media"/"player": they can match YouTube.
            "music" -> listOf("qf.musicplayer", "music player", "musicplayer", "muzic", "audio player")
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
                (action != "music" ||
                    (!text.contains("youtube") && !text.contains("google.android.apps.youtube"))) &&
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
        if (autoWeather()) {
            gpsWeather.start()
            return
        }
        gpsWeather.stop()
        refreshManualWeather()
    }

    private fun refreshManualWeather() {
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
                if (!autoWeather()) emitJs("updateWeather(${JSONObject.quote(city)},${Math.round(value)},${JSONObject.quote(label)});")
            } catch (_: Exception) {
                if (!autoWeather()) emitJs("updateWeather(${JSONObject.quote(city)},null,'');")
            } finally {
                connection?.disconnect()
            }
        }.start()
    }

    /**
     * Android battery indicator, not vehicle 12 V CANBUS voltage.
     * Car head units can have no Android battery sensor: unknown stays unknown.
     */
    /**
     * Firmware QF001 verified from original SystemUI DEX:
     * StatusBar.setBatteryPowerStatus reads sys.qf.update_battery_power (int),
     * BatteryPowerView.updateBatteryPower converts decivolts to volts (value * 0.1).
     *
     * We invoke /system/bin/getprop READ-ONLY, without root or hidden API access.
     * Android/SELinux may deny access to this system property for a normal app.
     * Absence/denial/invalid values are not replaced with guessed voltage.
     */
    private fun readQf001VehicleVoltage(): JSONObject {
        val result = JSONObject().apply {
            put("available", false)
            put("volts", JSONObject.NULL)
            put("source", "QF001_SYSTEM_PROPERTY")
            put("property", "sys.qf.update_battery_power")
            put("reason", "unavailable")
        }
        var process: Process? = null
        try {
            process = ProcessBuilder(
                "/system/bin/getprop", "sys.qf.update_battery_power"
            ).redirectErrorStream(true).start()
            val finished = process.waitFor(800, java.util.concurrent.TimeUnit.MILLISECONDS)
            if (!finished) {
                result.put("reason", "timeout")
                return result
            }
            if (process.exitValue() != 0) {
                result.put("reason", "getprop_denied")
                return result
            }
            val raw = process.inputStream.bufferedReader().use { it.readText() }.trim()
            val decivolts = raw.toIntOrNull()
            // Sanity bounds for conventional 12 V car battery / charging system.
            // 0, negative, non-numeric or unexpected values mean unverified.
            if (decivolts == null || decivolts !in 90..165) {
                result.put("reason", "missing_or_invalid_value")
                return result
            }
            result.put("volts", decivolts / 10.0)
            result.put("available", true)
            result.put("reason", "ok")
        } catch (_: SecurityException) {
            result.put("reason", "permission_denied")
        } catch (_: Exception) {
            result.put("reason", "getprop_not_accessible")
        } finally {
            process?.destroy()
        }
        return result
    }

    private fun androidBatterySnapshot(): JSONObject {
        val info = JSONObject().apply {
            put("source", "ANDROID")
            put("percent", JSONObject.NULL)
            put("charging", JSONObject.NULL)
            put("vehicleVoltage", JSONObject.NULL)
            put("vehicleVoltageAvailable", false)
        }
        try {
            val intent = registerReceiver(null,
                android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            if (intent != null) {
                val level = intent.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1)
                val scale = intent.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1)
                if (level >= 0 && scale > 0 && level <= scale) {
                    info.put("percent", (level * 100.0 / scale).toInt())
                }
                val status = intent.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1)
                if (status == android.os.BatteryManager.BATTERY_STATUS_CHARGING ||
                    status == android.os.BatteryManager.BATTERY_STATUS_FULL)
                    info.put("charging", true)
                else if (status == android.os.BatteryManager.BATTERY_STATUS_DISCHARGING ||
                    status == android.os.BatteryManager.BATTERY_STATUS_NOT_CHARGING)
                    info.put("charging", false)
            }
        } catch (_: Exception) {
            // Absent/unsupported Android battery sensor must not become car voltage.
        }
        return info
    }

    /** Nullable states: do not claim Wi-Fi/Bluetooth is on when access is denied. */
    private fun connectivitySnapshot(): JSONObject = BidConnectivity.snapshot(this)

    private fun themeApps(): List<android.content.pm.ResolveInfo> =
        packageManager.queryIntentActivities(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER),0)
            .filter { it.activityInfo.exported && it.activityInfo.enabled && it.activityInfo.packageName != packageName }
            .distinctBy { it.activityInfo.packageName + "/" + it.activityInfo.name }
            .sortedBy { it.loadLabel(packageManager).toString().lowercase(java.util.Locale.ROOT) }

    private fun themeAppEntry(key:String): android.content.pm.ResolveInfo? =
        if(key.length > 512) null else themeApps().firstOrNull {
            it.activityInfo.packageName + "/" + it.activityInfo.name == key
        }

    inner class Bridge {
        @JavascriptInterface
        fun listThemeApps(): String {
            val result=org.json.JSONArray()
            try { for (app in themeApps()) {
                result.put(JSONObject().put("key",app.activityInfo.packageName+"/"+app.activityInfo.name)
                    .put("label",app.loadLabel(packageManager).toString().take(100)))
            }} catch (_:Exception) {}
            return result.toString()
        }

        @JavascriptInterface
        fun themeAppIcon(key:String): String {
            return try {
                val entry=themeAppEntry(key) ?: return ""
                val icon=entry.loadIcon(packageManager)
                val bmp=android.graphics.Bitmap.createBitmap(96,96,android.graphics.Bitmap.Config.ARGB_8888)
                try {
                    icon.setBounds(0,0,96,96);icon.draw(android.graphics.Canvas(bmp))
                    val bytes=java.io.ByteArrayOutputStream()
                    bmp.compress(android.graphics.Bitmap.CompressFormat.PNG,100,bytes)
                    "data:image/png;base64,"+android.util.Base64.encodeToString(bytes.toByteArray(),android.util.Base64.NO_WRAP)
                } finally { bmp.recycle() }
            } catch (_:Exception) { "" }
        }

        @JavascriptInterface
        fun launchThemeApp(key:String) = runOnUiThread {
            if(webView.url != "file:///android_asset/index.html") return@runOnUiThread
            val app=try { themeAppEntry(key) } catch (_:Exception) { null }
            if(app==null) {
                Toast.makeText(this@MainActivity,"Aplicația nu mai este disponibilă.",Toast.LENGTH_SHORT).show()
            } else {
                startSafely(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
                    .setClassName(app.activityInfo.packageName,app.activityInfo.name)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
        }

        @JavascriptInterface
        fun displaySnapshot(): String = adaptiveDisplay.snapshot().toString()

        @JavascriptInterface
        fun setDisplayMode(mode: String) = adaptiveDisplay.apply(mode)

        @JavascriptInterface
        fun connectivitySnapshot(): String = this@MainActivity.connectivitySnapshot().toString()

        @JavascriptInterface
        fun batterySnapshot(): String = androidBatterySnapshot().toString()

        @JavascriptInterface
        fun vehicleVoltageSnapshot(): String = readQf001VehicleVoltage().toString()

        @JavascriptInterface
        fun chooseWeatherCity() = runOnUiThread {
            val choices = (listOf("Automat · GPS") + weatherCities.keys).toTypedArray()
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Vreme BID · alege localitatea")
                .setItems(choices) { _, index ->
                    val edit = getSharedPreferences("bid_weather", MODE_PRIVATE).edit()
                    edit.putBoolean("gps", index == 0)
                    if (index > 0) edit.putString("city", choices[index])
                    edit.apply()
                    if (index == 0 && !hasLocation()) askGpsOnce(true)
                    else if (index == 0 && android.os.Build.VERSION.SDK_INT >= 28 &&
                        !(getSystemService(LOCATION_SERVICE) as android.location.LocationManager).isLocationEnabled)
                        startSafely(Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS))
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
                // Inventory only: inspect Android-declared components without sending
                // broadcasts, binding to OEM services, or accessing MCU interfaces.
                val qfComponents = org.json.JSONArray()
                try {
                    @Suppress("DEPRECATION")
                    val pkg = packageManager.getPackageInfo(
                        vehiclePackage,
                        android.content.pm.PackageManager.GET_ACTIVITIES or
                            android.content.pm.PackageManager.GET_SERVICES or
                            android.content.pm.PackageManager.GET_RECEIVERS or
                            android.content.pm.PackageManager.GET_PROVIDERS
                    )
                    fun addComponents(kind: String, entries: Array<out android.content.pm.ComponentInfo>?) {
                        for (entry in entries ?: emptyArray()) {
                            if (!entry.exported) continue
                            qfComponents.put(JSONObject().apply {
                                put("type", kind)
                                put("name", entry.name)
                                put("exported", entry.exported)
                                put("permission", when (entry) {
                                    is android.content.pm.ActivityInfo -> entry.permission
                                    is android.content.pm.ServiceInfo -> entry.permission
                                    is android.content.pm.ProviderInfo -> entry.readPermission
                                    else -> null
                                } ?: "")
                            })
                        }
                    }
                    addComponents("activity", pkg.activities)
                    addComponents("service", pkg.services)
                    addComponents("receiver", pkg.receivers)
                    addComponents("provider", pkg.providers)
                } catch (_: Exception) {
                    // Package visibility and OEM restrictions can deny this inspection.
                }
                put("canbusExportedComponents", qfComponents)
                put("canbusInventoryReadOnly", true)

                put("canbusDataBridgeVerified", false)
                put("climatronicLiveAvailable", false)
                val qfVoltage = readQf001VehicleVoltage()
                put("carBatteryVoltageAvailable", qfVoltage.optBoolean("available", false))
                put("qf001VehicleVoltage", qfVoltage)
                put("androidBattery", androidBatterySnapshot())
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

        /**
         * Discover original QF001 apps through the Android launcher registry.
         * Never invoke non-exported/system-only components or hidden MCU APIs.
         * Safety-critical OEM functions (reverse camera etc.) remain OEM controlled.
         */
        /**
         * BID multimedia menu: launch only published/exported OEM activities.
         * No private MCU APIs, forced package installation, or privileged calls.
         */
        @JavascriptInterface
        fun openMediaOem(kind: String) = runOnUiThread {
            if (kind == "music" || kind == "radio" || kind == "dsp") {
                // The OEM QF001 music player wins over an old accidental YouTube association.
                val userChoice = assignedIntent(kind)
                val safeChoice = if (kind == "music" && userChoice != null &&
                    (userChoice.component?.packageName ?: "").contains("youtube", ignoreCase = true))
                    null else userChoice
                val target = if (kind == "music")
                    originalQf001Intent(kind) ?: safeChoice
                else safeChoice ?: originalQf001Intent(kind)
                if (target != null) {
                    startSafely(target)
                } else chooseAutoApp(kind)
                return@runOnUiThread
            }
            if (kind == "btaudio") {
                val target = assignedIntent("btcar") ?: originalQf001Intent("btcar")
                if (target != null) startSafely(target)
                else chooseAutoApp("btcar")
                return@runOnUiThread
            }
            val keys = when (kind) {
                "video" -> listOf("videoplayer", "video player", "com.qf.video")
                "files" -> listOf("fileexplorer", "file explorer", "file manager", "com.qf.file")
                "gallery" -> listOf("imagebrowser", "image browser", "gallery")
                "gps" -> listOf("beidougps", "gps info", "gpsinfo", "gps test")
                "tpms" -> listOf("tpms", "tire pressure", "tyre pressure")
                "steering" -> listOf("keystudy", "key study", "steering wheel")
                "weather" -> listOf("com.qf.weather", "weather", "vreme")
                "manual" -> listOf("qf.manual", "manual")
                else -> emptyList()
            }
            if (keys.isEmpty()) return@runOnUiThread
            val candidates = packageManager.queryIntentActivities(
                Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
            ).filter { result ->
                result.activityInfo.exported && keys.any { key ->
                    (result.loadLabel(packageManager).toString() + " " +
                        result.activityInfo.packageName).lowercase(java.util.Locale.ROOT).contains(key)
                }
            }
            if (candidates.isEmpty()) {
                Toast.makeText(this@MainActivity,
                    "Aplicația originală nu este disponibilă pentru lansare: " + kind,
                    Toast.LENGTH_LONG).show()
            } else if (candidates.size == 1) {
                val a = candidates.first().activityInfo
                startSafely(Intent(Intent.ACTION_MAIN)
                    .addCategory(Intent.CATEGORY_LAUNCHER)
                    .setClassName(a.packageName, a.name))
            } else {
                android.app.AlertDialog.Builder(this@MainActivity)
                    .setTitle("BID · Selectează aplicația")
                    .setItems(candidates.map { it.loadLabel(packageManager).toString() }.toTypedArray()) { _, pos ->
                        val a = candidates[pos].activityInfo
                        startSafely(Intent(Intent.ACTION_MAIN)
                            .addCategory(Intent.CATEGORY_LAUNCHER)
                            .setClassName(a.packageName, a.name))
                    }.setNegativeButton("Închide", null).show()
            }
        }

        /**
         * QF001 functions drawer: same 5 x 2 paged app-grid presentation as Apps.
         * Three fixed, swipeable sections; dynamically resolves real OEM icons
         * from exported launcher entries. Missing apps remain clearly unavailable.
         */
        @JavascriptInterface
        fun showFunctionsGrid() = runOnUiThread {
            data class FunctionTile(val label: String, val key: String, val matches: List<String>)
            val sections = listOf(
                "Multimedia" to listOf(
                    FunctionTile("Radio FM","radio",listOf("fmradio","radio")),
                    FunctionTile("Muzică","music",listOf("musicplayer","muzică","music")),
                    FunctionTile("Bluetooth / Telefon","btaudio",listOf("qf.bluetooth","bluetooth")),
                    FunctionTile("Muzică Bluetooth","btaudio",listOf("bt music","bluetooth music")),
                    FunctionTile("Video","video",listOf("videoplayer","video")),
                    FunctionTile("DSP / Egalizator","dsp",listOf("soundeffect","dsp")),
                    FunctionTile("Fișiere USB","files",listOf("fileexplorer","file manager")),
                    FunctionTile("Galerie","gallery",listOf("imagebrowser","gallery")),
                    FunctionTile("YouTube","youtube",listOf("youtube")),
                    FunctionTile("AUX","aux",listOf("aux"))
                ),
                "Mașină" to listOf(
                    FunctionTile("Setări auto","car",listOf("carsettings","carsetting")),
                    FunctionTile("Informații CANBUS","canbus",listOf("qf.vehicle","canbus")),
                    FunctionTile("Cameră marșarier","reverse",listOf("backcar","rear camera")),
                    FunctionTile("TPMS","tpms",listOf("tpms")),
                    FunctionTile("Comenzi volan","steering",listOf("keystudy","key study")),
                    FunctionTile("Bluetooth auto","btaudio",listOf("qf.bluetooth","bluetooth")),
                    FunctionTile("DSP auto","dsp",listOf("soundeffect","dsp"))
                ),
                "Navigație și utilitare" to listOf(
                    FunctionTile("GPS / Sateliți","gps",listOf("beidougps","gpsinfo")),
                    FunctionTile("Hărți","maps",listOf("maps")),
                    FunctionTile("Waze","waze",listOf("waze")),
                    FunctionTile("Fișiere / USB","files",listOf("fileexplorer","file manager")),
                    FunctionTile("Galerie foto","gallery",listOf("imagebrowser","gallery")),
                    FunctionTile("Vreme","weather",listOf("weather","vreme")),
                    FunctionTile("Manual","manual",listOf("manual")),
                    FunctionTile("Toate aplicațiile","apps",emptyList()),
                    FunctionTile("Permisiuni indicatoare","indicatorpermissions",emptyList())
                )
            )
            val launcherEntries = packageManager.queryIntentActivities(
                Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
            ).filter { it.activityInfo.exported && it.activityInfo.packageName != packageName }
            val screen = resources.displayMetrics
            val width = screen.widthPixels
            val height = screen.heightPixels
            val density = screen.density
            val px: (Float) -> Int = { (it * density).toInt() }
            val dialog = android.app.Dialog(this@MainActivity)
            val root = android.widget.LinearLayout(this@MainActivity).apply {
                orientation = android.widget.LinearLayout.VERTICAL
                setBackground(android.graphics.drawable.GradientDrawable(
                    android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
                    intArrayOf(0xFF180B12.toInt(),0xFF4D192B.toInt(),0xFF110A10.toInt())))
            }
            val heading = android.widget.TextView(this@MainActivity).apply {
                text = "BID · Funcții originale QF001"
                textSize = 23f
                setTextColor(0xFFFFDEAE.toInt())
                gravity = android.view.Gravity.CENTER
                setOnClickListener { dialog.dismiss() }
            }
            root.addView(heading,android.widget.LinearLayout.LayoutParams(-1,px(56f)))
            val carousel = android.widget.HorizontalScrollView(this@MainActivity).apply {
                isHorizontalScrollBarEnabled = false
                isFillViewport = false
                overScrollMode = View.OVER_SCROLL_NEVER
            }
            val pages = android.widget.LinearLayout(this@MainActivity).apply {
                orientation = android.widget.LinearLayout.HORIZONTAL
            }
            val pageHeight = (height - px(124f)).coerceAtLeast(px(250f))
            sections.forEach { (category, tiles) ->
                val page = android.widget.LinearLayout(this@MainActivity).apply {
                    orientation = android.widget.LinearLayout.VERTICAL
                }
                val sectionLabel = android.widget.TextView(this@MainActivity).apply {
                    text = category
                    textSize = 19f
                    gravity = android.view.Gravity.CENTER
                    setTextColor(0xFFEAC189.toInt())
                }
                page.addView(sectionLabel,android.widget.LinearLayout.LayoutParams(-1,px(34f)))
                val grid = android.widget.GridLayout(this@MainActivity).apply {
                    columnCount = 5
                    rowCount = 2
                }
                val cellWidth = width / 5
                val cellHeight = (pageHeight - px(34f)) / 2
                repeat(10) { i ->
                    val tile = tiles.getOrNull(i)
                    val cell = android.widget.LinearLayout(this@MainActivity).apply {
                        orientation = android.widget.LinearLayout.VERTICAL
                        gravity = android.view.Gravity.CENTER
                        setPadding(px(4f),px(4f),px(4f),px(4f))
                    }
                    if(tile != null) {
                        val matched = launcherEntries.firstOrNull { entry ->
                            val haystack = (entry.activityInfo.packageName + " " +
                                entry.loadLabel(packageManager)).lowercase(java.util.Locale.ROOT)
                            tile.matches.any { haystack.contains(it.lowercase(java.util.Locale.ROOT)) }
                        }
                        val image = android.widget.ImageView(this@MainActivity).apply {
                            setImageDrawable(matched?.loadIcon(packageManager)
                                ?: getDrawable(android.R.drawable.ic_menu_manage))
                            alpha = if(matched == null && tile.key !in listOf("apps","reverse","car","canbus","indicatorpermissions")) .55f else 1f
                            scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
                        }
                        cell.addView(image,android.widget.LinearLayout.LayoutParams(
                            minOf(px(110f),(cellWidth*.66f).toInt()),
                            minOf(px(110f),(cellHeight*.60f).toInt())))
                        val label = android.widget.TextView(this@MainActivity).apply {
                            text = tile.label
                            textSize = 16f
                            maxLines = 2
                            gravity = android.view.Gravity.CENTER
                            setTextColor(android.graphics.Color.WHITE)
                        }
                        cell.addView(label,android.widget.LinearLayout.LayoutParams(-1,px(46f)))
                        cell.setOnClickListener {
                            dialog.dismiss()
                            when(tile.key) {
                                "reverse" -> Toast.makeText(this@MainActivity,
                                    "Camera marșarier este controlată automat de QF001 în treapta R.",
                                    Toast.LENGTH_LONG).show()
                                "apps" -> showApps()
                                "indicatorpermissions" -> openIndicatorPermissions()
                                "car","canbus","maps","waze","youtube" -> Bridge().open(tile.key)
                                else -> Bridge().openMediaOem(tile.key)
                            }
                        }
                    }
                    grid.addView(cell,android.widget.GridLayout.LayoutParams(
                        android.widget.GridLayout.spec(i/5),android.widget.GridLayout.spec(i%5)
                    ).apply { this.width = cellWidth;this.height = cellHeight })
                }
                page.addView(grid,android.widget.LinearLayout.LayoutParams(-1,0,1f))
                pages.addView(page,android.widget.LinearLayout.LayoutParams(width,pageHeight))
            }
            carousel.addView(pages)
            root.addView(carousel,android.widget.LinearLayout.LayoutParams(-1,0,1f))
            val dots = android.widget.LinearLayout(this@MainActivity).apply {
                gravity = android.view.Gravity.CENTER
            }
            val dotLabels = sections.indices.map { index ->
                android.widget.TextView(this@MainActivity).apply {
                    text = "●"
                    textSize = 21f
                    setPadding(px(10f),0,px(10f),0)
                    setOnClickListener { carousel.smoothScrollTo(index*width,0) }
                    dots.addView(this)
                }
            }
            fun updateDots() {
                val active = ((carousel.scrollX+width/2)/width).coerceIn(0,sections.size-1)
                dotLabels.forEachIndexed { index,v ->
                    v.setTextColor(if(index==active)0xFFE7BA82.toInt() else 0xFF8B7180.toInt())
                }
            }
            carousel.setOnTouchListener { _, event ->
                if(event.actionMasked == android.view.MotionEvent.ACTION_UP ||
                    event.actionMasked == android.view.MotionEvent.ACTION_CANCEL) {
                    carousel.postDelayed({
                        val page = ((carousel.scrollX+width/2)/width).coerceIn(0,sections.size-1)
                        carousel.smoothScrollTo(page*width,0)
                    },90)
                }
                false
            }
            carousel.setOnScrollChangeListener { _,_,_,_,_ -> updateDots() }
            root.addView(dots,android.widget.LinearLayout.LayoutParams(-1,px(50f)))
            dialog.setContentView(root)
            dialog.show()
            dialog.window?.apply {
                setBackgroundDrawableResource(android.R.color.transparent)
                setLayout(width,height)
            }
            updateDots()
        }

        @JavascriptInterface
        fun showOemFunctions() = runOnUiThread {
            val categories = linkedMapOf(
                "Radio FM" to listOf("radio", "fmradio", "tuner"),
                "Muzică / Player audio" to listOf("music", "muzic", "audio player"),
                "Bluetooth / Telefon" to listOf("bluetooth", "handsfree", "bt phone", "bt music"),
                "DSP / Egalizator" to listOf("soundeffect", "dsp", "equalizer", "sound effect"),
                "Setări auto / CANBUS" to listOf("carsettings", "carsetting", "canbus", "car settings"),
                "Player video" to listOf("video player", "videoplayer"),
                "Fișiere / USB" to listOf("fileexplorer", "file explorer", "files", "file manager"),
                "Galerie imagini" to listOf("imagebrowser", "gallery", "image browser"),
                "GPS / Sateliți" to listOf("beidougps", "gps info", "gpsinfo"),
                "TPMS / Presiune pneuri" to listOf("tpms", "tire pressure", "tyre pressure"),
                "Comenzi volan" to listOf("keystudy", "key study", "steering wheel"),
                "Manual navigație" to listOf("qf.manual", "manual"),
                "Vreme OEM" to listOf("weather", "vreme"),
                "Cameră marșarier (OEM)" to listOf("backcar", "rear camera", "rearview")
            )
            val exported = packageManager.queryIntentActivities(
                Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
            ).filter { it.activityInfo.exported && it.activityInfo.packageName != packageName }
            val rows = mutableListOf<Pair<String, Intent?>>()
            categories.forEach { (name, keys) ->
                val app = exported.firstOrNull { candidate ->
                    val haystack = (candidate.loadLabel(packageManager).toString() +
                        " " + candidate.activityInfo.packageName).lowercase(java.util.Locale.ROOT)
                    keys.any { haystack.contains(it) }
                }
                if (app != null) {
                    val activity = app.activityInfo
                    val intent = Intent(Intent.ACTION_MAIN)
                        .addCategory(Intent.CATEGORY_LAUNCHER)
                        .setClassName(activity.packageName, activity.name)
                    rows.add(name + " · disponibil" to intent)
                } else rows.add(name + " · indisponibil pentru lansare" to null)
            }
            rows.add("Toate aplicațiile instalate" to null)
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("BID · Funcții originale QF001")
                .setItems(rows.map { it.first }.toTypedArray()) { _, index ->
                    if (index == rows.lastIndex) showApps()
                    else {
                        val selected = rows[index].second
                        if (selected != null) startSafely(selected)
                        else Toast.makeText(this@MainActivity,
                            "Această funcție nu oferă o interfață publică de lansare.",
                            Toast.LENGTH_LONG).show()
                    }
                }.setNegativeButton("Închide", null).show()
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
                "playstore" -> openPreferred("com.android.vending", "market://details?id=com.google.android.youtube", "https://play.google.com/store")
                "chrome" -> openPreferred("com.android.chrome", "https://www.google.com", "https://www.google.com")
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

    /**
     * BID app drawer mirrors the photographed QF001 layout: 5 icons across,
     * 2 rows per page, horizontal swiping and page dots. All entries come from
     * the installed Android launcher activities, never hard-coded screenshots.
     */
    private fun showApps() {
        val appsDiscovered = packageManager.queryIntentActivities(
            Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER), 0
        ).filter { it.activityInfo.packageName != packageName }
            .distinctBy { it.activityInfo.packageName + "/" + it.activityInfo.name }
            .sortedBy { it.loadLabel(packageManager).toString().lowercase(java.util.Locale.ROOT) }
        // The order survives app launches/restarts; newly installed apps append automatically.
        val orderPrefs = getSharedPreferences("bid_app_grid_order", MODE_PRIVATE)
        val savedOrder = orderPrefs.getString("ordered_components", "")!!
            .split("\\n").filter { it.isNotBlank() }
        val positions = savedOrder.withIndex().associate { it.value to it.index }
        fun appKey(app: android.content.pm.ResolveInfo): String =
            app.activityInfo.packageName + "/" + app.activityInfo.name
        val apps = appsDiscovered.sortedWith(compareBy<android.content.pm.ResolveInfo>(
            { positions[appKey(it)] ?: Int.MAX_VALUE },
            { it.loadLabel(packageManager).toString().lowercase(java.util.Locale.ROOT) }
        ))
        fun moveApp(draggedKey: String, targetKey: String) {
            val ordered = apps.map(::appKey).toMutableList()
            val old = ordered.indexOf(draggedKey)
            val target = ordered.indexOf(targetKey)
            if (old < 0 || target < 0 || old == target) return
            ordered.removeAt(old)
            ordered.add(ordered.indexOf(targetKey), draggedKey)
            orderPrefs.edit().putString("ordered_components", ordered.joinToString("\\n")).apply()
        }
        if (apps.isEmpty()) {
            Toast.makeText(this, "Nu sunt aplicații lansabile vizibile", Toast.LENGTH_LONG).show()
            return
        }
        val density = resources.displayMetrics.density
        val screen = resources.displayMetrics
        val width = screen.widthPixels
        val height = screen.heightPixels
        val px: (Float) -> Int = { (it * density).toInt() }
        val pageCount = (apps.size + 9) / 10
        val dialog = android.app.Dialog(this).apply {
            window?.setBackgroundDrawableResource(android.R.color.transparent)
        }
        val root = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setBackground(android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
                intArrayOf(0xFF160910.toInt(), 0xFF431527.toInt(), 0xFF12080F.toInt())
            ))
        }
        val top = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            setPadding(px(20f), px(6f), px(20f), px(4f))
        }
        val heading = android.widget.TextView(this).apply {
            text = "⌂   DJ 88 BID  ·  Aplicații"
            textSize = 21f
            setTextColor(0xFFFFE3B2.toInt())
        }
        top.addView(heading, android.widget.LinearLayout.LayoutParams(0, px(48f), 1f))
        val close = android.widget.TextView(this).apply {
            text = "↩"
            textSize = 35f
            gravity = android.view.Gravity.CENTER
            setTextColor(android.graphics.Color.WHITE)
            setOnClickListener { dialog.dismiss() }
        }
        top.addView(close, android.widget.LinearLayout.LayoutParams(px(68f), px(48f)))
        root.addView(top)
        val trash = android.widget.TextView(this).apply {
            text = "🗑  Trage aici pentru dezinstalare"
            gravity = android.view.Gravity.CENTER
            textSize = 18f
            setTextColor(android.graphics.Color.WHITE)
            setBackgroundColor(0xFF8F2028.toInt())
            visibility = View.GONE
            setOnDragListener { _, event ->
                when (event.action) {
                    android.view.DragEvent.ACTION_DRAG_ENTERED -> {
                        setBackgroundColor(0xFFCF333D.toInt())
                        true
                    }
                    android.view.DragEvent.ACTION_DRAG_EXITED -> {
                        setBackgroundColor(0xFF8F2028.toInt())
                        true
                    }
                    android.view.DragEvent.ACTION_DROP -> {
                        val targetKey = event.localState as? String
                        val targetPkg = targetKey?.substringBefore("/")
                        if (targetPkg != null && targetPkg != packageName) {
                            // ACTION_DELETE always delegates to the Android uninstall UI.
                            // System apps may only offer disable, or refuse removal.
                            try {
                                startActivity(Intent(Intent.ACTION_DELETE,
                                    Uri.parse("package:" + targetPkg)))
                                dialog.dismiss()
                            } catch (_: Exception) {
                                Toast.makeText(this@MainActivity,
                                    "Android nu permite dezinstalarea acestei aplicații",
                                    Toast.LENGTH_LONG).show()
                            }
                        }
                        true
                    }
                    android.view.DragEvent.ACTION_DRAG_ENDED -> {
                        visibility = View.GONE
                        setBackgroundColor(0xFF8F2028.toInt())
                        true
                    }
                    else -> true
                }
            }
        }
        root.addView(trash, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, px(54f)))

        val carousel = android.widget.HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = false
            isFillViewport = false
            overScrollMode = View.OVER_SCROLL_NEVER
        }
        val pages = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.HORIZONTAL
        }
        val pageHeight = (height - px(115f)).coerceAtLeast(px(260f))
        for (page in 0 until pageCount) {
            val grid = android.widget.GridLayout(this).apply {
                columnCount = 5
                rowCount = 2
                setPadding(px(18f), px(12f), px(18f), px(6f))
            }
            val cellWidth = (width - px(36f)) / 5
            val cellHeight = (pageHeight - px(18f)) / 2
            for (slot in 0 until 10) {
                val index = page * 10 + slot
                val cell = android.widget.LinearLayout(this).apply {
                    orientation = android.widget.LinearLayout.VERTICAL
                    gravity = android.view.Gravity.CENTER
                    setPadding(px(4f), px(4f), px(4f), px(4f))
                }
                if (index < apps.size) {
                    val info = apps[index]
                    val icon = android.widget.ImageView(this).apply {
                        setImageDrawable(info.loadIcon(packageManager))
                        scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
                    }
                    cell.addView(icon, android.widget.LinearLayout.LayoutParams(
                        minOf(px(132f), (cellWidth * .72f).toInt()),
                        minOf(px(132f), (cellHeight * .66f).toInt())))
                    val label = android.widget.TextView(this).apply {
                        text = info.loadLabel(packageManager)
                        textSize = 15f
                        maxLines = 2
                        gravity = android.view.Gravity.CENTER
                        ellipsize = android.text.TextUtils.TruncateAt.END
                        setTextColor(android.graphics.Color.WHITE)
                    }
                    cell.addView(label, android.widget.LinearLayout.LayoutParams(
                        cellWidth - px(10f), px(44f)))
                    cell.setOnLongClickListener { view ->
                        trash.visibility = View.VISIBLE
                        // Drag only package identity; never run silent uninstall.
                        val key = appKey(info)
                        val clip = android.content.ClipData.newPlainText(
                            "BID component", key)
                        view.startDragAndDrop(clip,
                            View.DragShadowBuilder(view), key, 0)
                        true
                    }
                    // Drop onto another icon to reorder. No uninstall occurs here.
                    cell.setOnDragListener { view, event ->
                        when (event.action) {
                            android.view.DragEvent.ACTION_DRAG_ENTERED -> {
                                view.alpha = .65f
                                true
                            }
                            android.view.DragEvent.ACTION_DRAG_EXITED,
                            android.view.DragEvent.ACTION_DRAG_ENDED -> {
                                view.alpha = 1f
                                true
                            }
                            android.view.DragEvent.ACTION_DROP -> {
                                view.alpha = 1f
                                val dragged = event.localState as? String
                                val target = appKey(info)
                                if (dragged != null && dragged != target) {
                                    moveApp(dragged, target)
                                    dialog.dismiss()
                                    showApps() // Reload saved order without changing wallpaper.
                                }
                                true
                            }
                            else -> true
                        }
                    }
                    cell.setOnClickListener {
                        val activity = info.activityInfo
                        dialog.dismiss()
                        startSafely(Intent(Intent.ACTION_MAIN).apply {
                            addCategory(Intent.CATEGORY_LAUNCHER)
                            setClassName(activity.packageName, activity.name)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        })
                    }
                }
                grid.addView(cell, android.widget.GridLayout.LayoutParams(
                    android.widget.GridLayout.spec(slot / 5),
                    android.widget.GridLayout.spec(slot % 5)
                ).apply {
                    this.width = cellWidth
                    this.height = cellHeight
                })
            }
            pages.addView(grid, android.widget.LinearLayout.LayoutParams(width, pageHeight))
        }
        carousel.addView(pages)
        root.addView(carousel, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))

        val dots = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER
        }
        val dotViews = (0 until pageCount).map { page ->
            android.widget.TextView(this).apply {
                text = "●"
                textSize = 18f
                gravity = android.view.Gravity.CENTER
                setPadding(px(3f), 0, px(3f), 0)
                setOnClickListener { carousel.smoothScrollTo(page * width, 0) }
                dots.addView(this)
            }
        }
        fun updateDots() {
            val index = ((carousel.scrollX + width / 2) / width).coerceIn(0, pageCount - 1)
            dotViews.forEachIndexed { i, v ->
                v.setTextColor(if (i == index) 0xFFD8B981.toInt() else 0xFFA9BDDF.toInt())
            }
        }
        carousel.setOnTouchListener { _, event ->
            if (event.actionMasked == android.view.MotionEvent.ACTION_UP ||
                event.actionMasked == android.view.MotionEvent.ACTION_CANCEL) {
                carousel.postDelayed({
                    val nearest = ((carousel.scrollX + width / 2) / width)
                        .coerceIn(0, pageCount - 1)
                    carousel.smoothScrollTo(nearest * width, 0)
                    carousel.postDelayed({ updateDots() }, 250)
                }, 100)
            }
            false
        }
        carousel.setOnScrollChangeListener { _, _, _, _, _ -> updateDots() }
        root.addView(dots, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT, px(44f)))
        dialog.setContentView(root)
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout(width, height)
            addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        }
        dialog.show()
        dialog.window?.setLayout(width, height)
        updateDots()
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
