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
    private val cache = context.getSharedPreferences("bid_weather_last_success", Context.MODE_PRIVATE)
    private var lastCity: String? = cache.getString("city", null)
    private var lastTemperature: Double? = cache.getString("temperature", null)?.toDoubleOrNull()?.takeIf { it.isFinite() }
    private var lastCode: Int? = cache.getInt("code", -1).takeIf { it >= 0 }
    private var lastDay: Boolean? = if (cache.contains("isDay")) cache.getBoolean("isDay", false) else null
    private var registeredProviders = mutableSetOf<String>()
    private var lastSuccessAt = 0L
    private var lastFetchSucceeded = false
    private var staleShown = false
    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            registerProviders()
            val fix = lastFix
            if (fix != null && usable(fix)) {
                maybeFetch(fix)
            } else if (!staleShown) {
                staleShown = true
                publish(lastCity, lastTemperature, lastCode, "GPS indisponibil · date neactualizate", false, lastDay)
            }
            if (lastSuccessAt > 0 && SystemClock.elapsedRealtime() - lastSuccessAt > 900_000L && !staleShown) {
                staleShown = true
                publish(lastCity, lastTemperature, lastCode, "Date meteo neactualizate", false)
            }
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
        if (!fine && !coarse) { publish(lastCity, lastTemperature, lastCode, "Permisiune GPS necesară", false, lastDay); return }
        running = true
        generation++
        lastRequest = null
        lastAt = 0
        staleShown = true
        publish(lastCity, lastTemperature, lastCode, "Se caută poziția GPS", false, lastDay)
        registerProviders()
        lastFix?.takeIf { usable(it) }?.let { maybeFetch(it) }
        handler.postDelayed(tick, 30_000)
    }

    private fun registerProviders() {
        val fine = context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarse = context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (!fine && !coarse) return
        val providers = if (fine) listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER)
            else listOf(LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER)
        for (provider in providers) {
            try {
                if (!manager.isProviderEnabled(provider)) { registeredProviders.remove(provider); continue }
                if (provider !in registeredProviders) {
                    manager.requestLocationUpdates(provider, 10_000L, 0f, listener, Looper.getMainLooper())
                    registeredProviders.add(provider)
                }
                manager.getLastKnownLocation(provider)?.takeIf { usable(it) }?.let {
                    if (lastFix == null || it.elapsedRealtimeNanos > lastFix!!.elapsedRealtimeNanos) lastFix = it
                }
            } catch (_: Exception) {}
        }
    }

    fun stop() {
        running = false
        generation++
        handler.removeCallbacks(tick)
        registeredProviders.clear()
        try { manager.removeUpdates(listener) } catch (_: Exception) {}
    }

    fun close() { stop(); worker.shutdownNow() }

    private fun maybeFetch(fix: Location) {
        if (!running || !usable(fix) || busy) return
        val now = SystemClock.elapsedRealtime()
        val moved = lastRequest?.distanceTo(fix) ?: Float.MAX_VALUE
        val elapsed = now - lastAt
        if (lastRequest != null && (if (!lastFetchSucceeded) elapsed < 30_000L else elapsed < 600_000L && (moved < 300f || elapsed < 60_000L))) return
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
            var isDay: Boolean? = null
            var connection: HttpURLConnection? = null
            try {
                if (Geocoder.isPresent()) {
                    @Suppress("DEPRECATION")
                    val address = Geocoder(context, Locale("ro", "RO")).getFromLocation(lat, lon, 1)?.firstOrNull()
                    city = listOf(address?.locality, address?.subLocality)
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
                isDay = when (current.optInt("is_day", -1)) { 1 -> true; 0 -> false; else -> null }
            } catch (_: Exception) {} finally { connection?.disconnect() }
            handler.post {
                busy = false
                if (!running || generation != token) return@post
                if (temperature != null) {
                    lastCity = city
                    lastTemperature = temperature
                    lastCode = code
                    lastDay = isDay
                    lastFetchSucceeded = true
                    cache.edit().putString("city", city).putString("temperature", temperature.toString())
                        .putInt("code", code ?: -1).putLong("savedAt", System.currentTimeMillis()).apply {
                            if (isDay == null) remove("isDay") else putBoolean("isDay", isDay == true)
                        }.apply()
                    lastSuccessAt = SystemClock.elapsedRealtime()
                    staleShown = false
                    publish(city, temperature, code, if (city == null) "Localitate neidentificată" else "Vreme după GPS", true, isDay)
                } else {
                    // Never label the previous location's temperature as current at the new location.
                    lastFetchSucceeded = false
                    staleShown = true
                    publish(lastCity, lastTemperature, lastCode, "Date meteo neactualizate", false, lastDay)
                }
            }
        }
    }

    private fun publish(city: String?, temp: Double?, code: Int?, note: String, fresh: Boolean, isDay: Boolean? = null) {
        val data = JSONObject().apply {
            put("city", city ?: JSONObject.NULL); put("temperature", temp ?: JSONObject.NULL)
            put("code", code ?: JSONObject.NULL); put("isDay", isDay ?: JSONObject.NULL); put("fresh", fresh); put("note", note)
            put("savedAt", cache.getLong("savedAt", 0L))
        }
        emit("if(window.updateGpsWeather){window.updateGpsWeather($data);}else if(window.updateWeather){window.updateWeather(" +
            JSONObject.quote(if (fresh) city ?: "GPS" else (city ?: "GPS") + " *") +
            "," + (temp?.toString() ?: "null") + "," + JSONObject.quote(note) + ");}")
    }
}
