package ro.dj88bid.car

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.webkit.WebView

/** Foreground GPS speed only. No storage, coordinates in JS, CANBUS, or network. */
class BidGpsSpeed(private val activity: Activity, private val web: WebView) : LocationListener {
    private val manager = activity.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
    private val handler = Handler(Looper.getMainLooper())
    private var running = false
    private var lastFix = 0L
    private fun emit(js: String) = web.evaluateJavascript(js, null)
    private fun unavailable() {
        lastFix = 0L
        emit("if(window.bidGpsSpeedUnavailable)window.bidGpsSpeedUnavailable();")
    }
    private val expiry = object : Runnable {
        override fun run() {
            if (!running) return
            if (lastFix == 0L || SystemClock.elapsedRealtime() - lastFix > 4000L) unavailable()
            handler.postDelayed(this, 1000L)
        }
    }
    fun start() {
        if (running) return
        unavailable()
        if (activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return
        try {
            val m = manager ?: return
            m.requestLocationUpdates(LocationManager.GPS_PROVIDER, 500L, 0f, this, Looper.getMainLooper())
            running = true
            handler.post(expiry)
        } catch (_: Exception) { unavailable() }
    }
    fun stop() {
        running = false
        handler.removeCallbacks(expiry)
        try { manager?.removeUpdates(this) } catch (_: Exception) {}
        unavailable()
    }
    override fun onLocationChanged(location: Location) {
        if (!running) return
        val age = SystemClock.elapsedRealtimeNanos() - location.elapsedRealtimeNanos
        if (location.provider != LocationManager.GPS_PROVIDER || age < 0 || age > 4_000_000_000L || !location.hasSpeed() || location.isFromMockProvider || !location.hasAccuracy() || location.accuracy > 50f || (Build.VERSION.SDK_INT >= 26 && location.hasSpeedAccuracy() && location.speedAccuracyMetersPerSecond > 3f)) {
            unavailable(); return
        }
        val speed = location.speed
        if (!speed.isFinite() || speed < 0f || speed > 100f) { unavailable(); return }
        lastFix = SystemClock.elapsedRealtime()
        emit("if(window.bidGpsSpeedUpdate)window.bidGpsSpeedUpdate(${speed.toDouble()});")
    }
    override fun onProviderDisabled(provider: String) { unavailable() }
    override fun onProviderEnabled(provider: String) {}
    @Suppress("DEPRECATION") override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
}
