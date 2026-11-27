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

/** Session-only map configuration. No location history or API key is stored. */
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
            generation++; mapKey = key.trim().take(200); metadataReady = false; metadataBusy = false
            endpoint = try {
                val u = Uri.parse(osmEndpoint.trim()); if (u.scheme == "https" && !u.host.isNullOrBlank() && u.userInfo == null && u.fragment == null && osmEndpoint.length <= 500) osmEndpoint.trim() else ""
            } catch (_: Exception) { "" }
            lastQueryAt = -120000L; lastLat = null; lastLon = null; queryBusy = false
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
                if (result == null) mapKey = ""
                emit("if(window.bidDriveMapMetadata)window.bidDriveMapMetadata(" + (result?.toString() ?: "null") + ");")
            }
        }
    }
    @JavascriptInterface fun disable() {
        activity.runOnUiThread { generation++; endpoint = ""; mapKey = ""; metadataReady = false; metadataBusy = false; queryBusy = false; lastLat = null; lastLon = null; lastQueryAt = -120000L }
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
