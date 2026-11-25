package ro.dj88bid.car

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Geocoder
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import java.util.concurrent.Executors

/** Foreground only. No route history. Coordinates sent only to the chosen weather service. */
internal class BidGpsWeather(
    private val context: Context,
    private val emit: (String) -> Unit
) {
    private val manager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val handler = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private var running = false
    private var generation = 0
    private var busy = false
    private var lastFix: Location? = null
    private var lastRequest: Location? = null
    private var lastAt = 0L
    private var lastCity: String? = null
    private var lastTemperature: Double? = null
    private var lastCode: Int? = null
    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            lastFix?.let { maybeFetch(it) }
            handler.postDelayed(this, 30_000)
        }
    }
    private val listener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            if (!running || !usable(location)) return
            lastFix = Location(location)
            maybeFetch(location)
        }
        override fun onProviderEnabled(provider: String) {}
        override fun onProviderDisabled(provider: String) {}
        @Suppress("DEPRECATION")
        override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    }

    private fun usable(fix: Location): Boolean =
        fix.elapsedRealtimeNanos > 0 &&
        SystemClock.elapsedRealtimeNanos() - fix.elapsedRealtimeNanos in 0L..120_000_000_000L &&
        (!fix.hasAccuracy() || fix.accuracy <= 1000f)

    fun start() {
        if (running) return
        val fine = context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarse = context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (!fine && !coarse) { publish(null, null, null, "Permisiune GPS necesară", false); return }
        running = true
        generation++
        lastRequest = null
        lastAt = 0
        publish(lastCity, lastTemperature, lastCode, "Se caută poziția GPS", false)
        val providers = if (fine) listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
            else listOf(LocationManager.NETWORK_PROVIDER)
        for (provider in providers) {
            try {
                if (!manager.isProviderEnabled(provider)) continue
                manager.requestLocationUpdates(provider, 15_000L, 100f, listener, Looper.getMainLooper())
                manager.getLastKnownLocation(provider)?.takeIf { usable(it) }?.let {
                    if (lastFix == null || it.elapsedRealtimeNanos > lastFix!!.elapsedRealtimeNanos) lastFix = it
                }
            } catch (_: Exception) {}
        }
        lastFix?.takeIf { usable(it) }?.let { maybeFetch(it) }
        handler.postDelayed(tick, 30_000)
    }

    fun stop() {
        running = false
        generation++
        handler.removeCallbacks(tick)
        try { manager.removeUpdates(listener) } catch (_: Exception) {}
    }

    fun close() { stop(); worker.shutdownNow() }

    private fun maybeFetch(fix: Location) {
        if (!running || !usable(fix) || busy) return
        val now = SystemClock.elapsedRealtime()
        val moved = lastRequest?.distanceTo(fix) ?: Float.MAX_VALUE
        val elapsed = now - lastAt
        if (lastRequest != null && elapsed < 600_000L && (moved < 300f || elapsed < 60_000L)) return
        lastRequest = Location(fix)
        lastAt = now
        busy = true
        val token = generation
        val lat = fix.latitude
        val lon = fix.longitude
        worker.execute {
            var city: String? = null
            var temperature: Double? = null
            var code: Int? = null
            var connection: HttpURLConnection? = null
            try {
                if (Geocoder.isPresent()) {
                    @Suppress("DEPRECATION")
                    val address = Geocoder(context, Locale("ro", "RO")).getFromLocation(lat, lon, 1)?.firstOrNull()
                    city = listOf(address?.locality, address?.subLocality, address?.subAdminArea)
                        .firstOrNull { !it.isNullOrBlank() }
                }
            } catch (_: Exception) {}
            try {
                val endpoint = "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon&current=temperature_2m,weather_code,is_day&timezone=auto"
                connection = (URL(endpoint).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 6000; readTimeout = 6000
                }
                val current = JSONObject(connection.inputStream.bufferedReader().use { it.readText() }).getJSONObject("current")
                temperature = current.getDouble("temperature_2m").takeIf { it.isFinite() }
                code = current.getInt("weather_code")
            } catch (_: Exception) {} finally { connection?.disconnect() }
            handler.post {
                busy = false
                if (!running || generation != token) return@post
                if (temperature != null) {
                    lastCity = city
                    lastTemperature = temperature
                    lastCode = code
                    publish(city, temperature, code, if (city == null) "Localitate neidentificată" else "Vreme după GPS", true)
                } else {
                    // Never label the previous location's temperature as current at the new location.
                    publish(lastCity, lastTemperature, lastCode, "Date meteo neactualizate", false)
                }
            }
        }
    }

    private fun publish(city: String?, temp: Double?, code: Int?, note: String, fresh: Boolean) {
        val data = JSONObject().apply {
            put("city", city ?: JSONObject.NULL); put("temperature", temp ?: JSONObject.NULL)
            put("code", code ?: JSONObject.NULL); put("fresh", fresh); put("note", note)
        }
        emit("if(window.updateGpsWeather){window.updateGpsWeather($data);}else if(window.updateWeather){window.updateWeather(" +
            JSONObject.quote(if (fresh) city ?: "GPS" else (city ?: "GPS") + " *") +
            "," + (temp?.toString() ?: "null") + "," + JSONObject.quote(note) + ");}")
    }
}
