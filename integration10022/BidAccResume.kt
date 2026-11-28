package ro.dj88bid.car

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.SystemClock
import android.util.Log

/**
 * Read-only standby diagnostics. Android HOME selection is the supported return
 * path. SCREEN_ON and POWER_CONNECTED are deliberately NOT labeled ACC.
 * No background activity launches, wake locks, or MCU writes.
 */
class BidAccResume(private val activity: Activity) {
    private var registered = false
    private val prefs = activity.getSharedPreferences("bid_acc_diagnostic", Context.MODE_PRIVATE)
    private val session = java.util.UUID.randomUUID().toString()
    private var lastAction = ""
    private var lastAt = -10000L
    private fun record(action: String) {
        val now = SystemClock.elapsedRealtime()
        if (action == lastAction && now - lastAt < 1000L) return
        lastAction = action
        lastAt = now
        val entry = org.json.JSONObject().apply {
            put("event", action)
            put("elapsedMs", now)
            put("wallMs", System.currentTimeMillis())
            put("processSession", session)
        }
        val history = try { org.json.JSONArray(prefs.getString("history", "[]")) } catch (_: Exception) { org.json.JSONArray() }
        val next = org.json.JSONArray()
        for (i in maxOf(0, history.length() - 63) until history.length()) next.put(history.get(i))
        next.put(entry)
        prefs.edit().putString("last_event", action)
            .putLong("last_elapsed_ms", now).putString("history", next.toString()).commit()
        Log.i("BID-ACC", action)
    }
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_SCREEN_ON -> record("screen_on")
                Intent.ACTION_SCREEN_OFF -> record("screen_off")
                Intent.ACTION_POWER_CONNECTED -> record("power_connected_not_acc")
                Intent.ACTION_POWER_DISCONNECTED -> record("power_disconnected_not_acc")
            }
        }
    }
    fun resumed() = record("activity_resumed")
    fun paused() = record("activity_paused")
    fun homeIntent() = record("home_intent_received")
    fun snapshot(): String = prefs.getString("history", "[]") ?: "[]"
    fun start() {
        if (registered) return
        record("activity_created")
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_POWER_CONNECTED)
            addAction(Intent.ACTION_POWER_DISCONNECTED)
        }
        try {
            if (Build.VERSION.SDK_INT >= 33)
                activity.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
            else activity.registerReceiver(receiver, filter)
            registered = true
        } catch (e: SecurityException) {
            Log.w("BID-ACC", "Receiver unavailable", e)
        }
    }
    fun close() {
        if (!registered) return
        try { activity.unregisterReceiver(receiver) } catch (_: IllegalArgumentException) {}
        registered = false
    }
}
