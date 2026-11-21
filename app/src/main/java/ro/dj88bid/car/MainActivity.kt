package ro.dj88bid.car

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
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

    inner class Bridge {
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
                    info.put("package", prefs.getString(key + "_pkg", "neconfigurat"))
                    info.put("available", assignedIntent(key) != null)
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
            val intent = assignedIntent(action)
            if (intent != null) startSafely(intent)
            else {
                Toast.makeText(this@MainActivity, "Asociază o aplicație pentru " + autoActions[action], Toast.LENGTH_LONG).show()
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
        fun open(command: String) = runOnUiThread {
            when (command) {
                "maps" -> openPreferred("com.google.android.apps.maps", "geo:0,0", "https://www.google.com/maps")
                "waze" -> openPreferred("com.waze", "waze://", "https://waze.com/ul")
                "youtube" -> openPreferred("com.google.android.youtube", "https://www.youtube.com", "https://www.youtube.com")
                "phone" -> startSafely(Intent(Intent.ACTION_DIAL, Uri.parse("tel:")))
                "bluetooth" -> startSafely(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                "settings" -> startSafely(Intent(Settings.ACTION_SETTINGS))
                "apps" -> showApps()
                "original" -> startSafely(Intent(Settings.ACTION_HOME_SETTINGS))
                else -> Toast.makeText(this@MainActivity, "Comandă necunoscută", Toast.LENGTH_SHORT).show()
            }
        }
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
