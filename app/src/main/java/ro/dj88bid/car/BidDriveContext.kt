package ro.dj88bid.car

import android.app.Activity
import android.location.Location
import android.net.Uri
import android.os.SystemClock
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import java.util.Locale
import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Provider configuration encrypted with Android Keystore. No location history stored. */
class BidDriveContext(private val activity: Activity, private val web: WebView) {
    private val worker = Executors.newSingleThreadExecutor()
    private var generation = 0
    private var endpoint = ""
    private var active = false
    private var lastQueryAt = -120000L
    private var queryBusy = false
    private var mapKey = ""
    private var lastLat: Double? = null
    private var lastLon: Double? = null
    private var metadataReady = false
    private var metadataBusy = false
    private val prefs = activity.getSharedPreferences("bid_drive_secure", Context.MODE_PRIVATE)
    private val alias = "bid_drive_provider_aes_v1"
    private var persisted = false
    private var storageError = false
    private var restored = false
    private fun secret(create: Boolean): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = ks.getKey(alias, null) as? SecretKey
        if (existing != null) return existing
        check(create) { "Missing provider key" }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build())
        }.generateKey()
    }
    private fun saveConfig(): Boolean = try {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, secret(true))
        val data = JSONObject().put("key", mapKey).put("endpoint", endpoint).toString().toByteArray(Charsets.UTF_8)
        val encrypted = cipher.doFinal(data)
        prefs.edit().putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .putString("cipher", Base64.encodeToString(encrypted, Base64.NO_WRAP)).commit()
    } catch (_: Exception) { false }
    private fun notifyConfig() {
        val state = JSONObject().put("key", mapKey).put("endpoint", endpoint)
            .put("saved", persisted).put("storageError", storageError)
        emit("if(window.bidDriveConfigState)window.bidDriveConfigState($state);")
    }
    @JavascriptInterface fun restore() {
        activity.runOnUiThread {
            if (!restored) {
                restored = true
                try {
                    val iv = prefs.getString("iv", null)
                    val enc = prefs.getString("cipher", null)
                    if (iv != null && enc != null) {
                        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                        cipher.init(Cipher.DECRYPT_MODE, secret(false), GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
                        val data = JSONObject(String(cipher.doFinal(Base64.decode(enc, Base64.NO_WRAP)), Charsets.UTF_8))
                        mapKey = data.optString("key"); endpoint = data.optString("endpoint"); persisted = true
                    }
                } catch (_: Exception) { storageError = true; mapKey = ""; endpoint = "" }
            }
            notifyConfig()
            if (active) metadata()
        }
    }
    private fun emit(js: String) { web.evaluateJavascript(js, null) }
    private fun request(url: URL, body: String? = null): String {
        val conn = url.openConnection() as HttpURLConnection
        try {
            conn.connectTimeout = 6000; conn.readTimeout = 6000
            conn.instanceFollowRedirects = false
            conn.useCaches = false
            conn.setRequestProperty("User-Agent", "DJ88-BID-SmartDrive-Lab/1.0")
            if (body != null) {
                conn.requestMethod = "POST"; conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
                conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            if (conn.responseCode != 200) throw java.io.IOException("Map provider unavailable")
            return conn.inputStream.bufferedReader().use { reader ->
                val result = StringBuilder(); val chunk = CharArray(4096)
                while (true) { val n = reader.read(chunk); if (n < 0) break; result.append(chunk, 0, n); if (result.length > 1_000_000) throw java.io.IOException("Response too large") }
                result.toString()
            }
        } finally { conn.disconnect() }
    }
    @JavascriptInterface fun configure(key: String, osmEndpoint: String) {
        activity.runOnUiThread {
            generation++; restored = true; if (key.isNotBlank()) mapKey = key.trim().take(200); metadataReady = false; metadataBusy = false
            endpoint = try {
                val u = Uri.parse(osmEndpoint.trim()); if (u.scheme == "https" && !u.host.isNullOrBlank() && u.userInfo == null && u.fragment == null && osmEndpoint.length <= 500) osmEndpoint.trim() else ""
            } catch (_: Exception) { "" }
            lastQueryAt = -120000L; lastLat = null; lastLon = null; queryBusy = false
            persisted = if (mapKey.isBlank() && endpoint.isBlank()) prefs.edit().clear().commit() else saveConfig()
            storageError = !persisted
            if (mapKey.isBlank() && endpoint.isBlank()) persisted = false
            notifyConfig()
            if (active) metadata()
        }
    }
    private fun metadata() {
        if (!active || mapKey.isBlank() || metadataReady || metadataBusy) return
        val token = generation; val key = mapKey; metadataBusy = true
        worker.execute {
            val result = try {
                val json = JSONObject(request(URL("https://api.maptiler.com/tiles/satellite-v2/tiles.json?key=" + Uri.encode(key))))
                val template = json.getJSONArray("tiles").getString(0)
                require(template.startsWith("https://api.maptiler.com/") && template.contains("{z}") && template.contains("{x}") && template.contains("{y}"))
                val attribution = json.getString("attribution"); require(attribution.isNotBlank())
                JSONObject().put("template", template).put("attribution", attribution).put("maxzoom", json.optInt("maxzoom",18))
            } catch (_: Exception) { null }
            activity.runOnUiThread {
                if (generation != token || !active) return@runOnUiThread
                metadataBusy = false; metadataReady = result != null
                // Keep saved configuration after transient network failure.
                emit("if(window.bidDriveMapMetadata)window.bidDriveMapMetadata(" + (result?.toString() ?: "null") + ");")
            }
        }
    }
    @JavascriptInterface fun disable() {
        activity.runOnUiThread { generation++; restored = true; endpoint = ""; mapKey = ""; metadataReady = false; metadataBusy = false; queryBusy = false; lastLat = null; lastLon = null; lastQueryAt = -120000L; persisted = false; storageError = !prefs.edit().clear().commit(); notifyConfig() }
    }
    fun start() { active = true; metadata() }
    fun stop() { active = false; generation++; queryBusy = false; metadataBusy = false; lastLat = null; lastLon = null }
    fun close() { stop(); worker.shutdownNow() }
    fun onFix(fix: Location) {
        if (!active) return
        val data = JSONObject().put("lat", fix.latitude).put("lon", fix.longitude).put("accuracy",fix.accuracy)
        if (fix.hasBearing()) data.put("bearing", fix.bearing)
        emit("if(window.bidDriveFix)window.bidDriveFix($data);")
        if (endpoint.isBlank() || queryBusy) return
        val now = SystemClock.elapsedRealtime()
        if (now - lastQueryAt < 30000L) return
        if (lastLat != null && lastLon != null) {
            val dist = FloatArray(1); Location.distanceBetween(lastLat!!, lastLon!!,fix.latitude,fix.longitude,dist)
            if (dist[0] < 150f && now - lastQueryAt < 90000L) return
        }
        val lat = String.format(Locale.US, "%.4f", fix.latitude); val lon = String.format(Locale.US, "%.4f",fix.longitude)
        val south = String.format(Locale.US, "%.5f", fix.latitude - 0.002)
        val north = String.format(Locale.US, "%.5f", fix.latitude + 0.002)
        val west = String.format(Locale.US, "%.5f", fix.longitude - 0.003)
        val east = String.format(Locale.US, "%.5f", fix.longitude + 0.003)
        val query = "[out:json][timeout:8];(nwr(around:130,$lat,$lon)[building];nwr(around:130,$lat,$lon)[landuse];nwr(around:130,$lat,$lon)[natural=wood];);out tags 100;way(around:130,$lat,$lon)[highway];out geom($south,$west,$north,$east) 80;"
        val queryFix = JSONObject().put("lat",fix.latitude).put("lon",fix.longitude).put("accuracy",fix.accuracy)
        val token = generation; val service = endpoint; queryBusy = true; lastQueryAt = now; lastLat = fix.latitude; lastLon = fix.longitude
        worker.execute {
            val result = try {
                val raw = JSONObject(request(URL(service), "data=" + java.net.URLEncoder.encode(query,"UTF-8"))).getJSONArray("elements")
                val out = JSONArray(); val roads = JSONArray()
                for (i in 0 until minOf(raw.length(),180)) {
                    val el = raw.optJSONObject(i) ?: continue
                    val t = el.optJSONObject("tags") ?: continue
                    if (t.has("highway") && el.optJSONArray("geometry") != null) {
                        roads.put(JSONObject().put("highway",t.optString("highway")).put("geometry",el.getJSONArray("geometry")))
                    } else {
                        val filtered = JSONObject(); for (k in listOf("building","landuse","natural")) if (t.has(k)) filtered.put(k,t.optString(k)); out.put(filtered)
                    }
                }; JSONObject().put("tags",out).put("roads",roads).put("fix",queryFix)
            } catch (_: Exception) { JSONObject().put("tags",JSONArray()).put("roads",JSONArray()).put("fix",queryFix) }
            activity.runOnUiThread { if (generation == token && active) { queryBusy = false; emit("if(window.bidDriveContext)window.bidDriveContext($result);") } }
        }
    }
}
