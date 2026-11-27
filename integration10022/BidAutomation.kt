package ro.dj88bid.car

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.bluetooth.BluetoothDevice
import android.os.Build
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject

class BidAutomation(private val activity: Activity, private val web: WebView) {
    private val prefs = activity.getSharedPreferences("bid_automation", Context.MODE_PRIVATE)
    private var registered = false
    private val keys = setOf("power", "bluetooth")
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val kind = when (intent.action) {
                Intent.ACTION_POWER_CONNECTED -> "power_connected"
                Intent.ACTION_POWER_DISCONNECTED -> "power_disconnected"
                BluetoothDevice.ACTION_ACL_CONNECTED -> "bluetooth_connected"
                BluetoothDevice.ACTION_ACL_DISCONNECTED -> "bluetooth_disconnected"
                else -> return
            }
            val group = if (kind.startsWith("power")) "power" else "bluetooth"
            if (!prefs.getBoolean(group, false)) return
            if (web.url != "file:///android_asset/index.html" || activity.isFinishing) return
            val data = JSONObject().put("event", kind).put("at", System.currentTimeMillis())
            web.evaluateJavascript("if(window.bidAutomationEvent)window.bidAutomationEvent("+data.toString()+");",null)
        }
    }

    @JavascriptInterface fun enabled(key: String): Boolean =
        key in keys && prefs.getBoolean(key, false)

    @JavascriptInterface fun configure(key: String, enabled: Boolean) {
        activity.runOnUiThread {
            if (key in keys && web.url == "file:///android_asset/index.html" && activity.hasWindowFocus()) {
                prefs.edit().putBoolean(key, enabled).apply()
            }
        }
    }

    fun start() {
        if (registered) return
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_POWER_CONNECTED)
            addAction(Intent.ACTION_POWER_DISCONNECTED)
            addAction(BluetoothDevice.ACTION_ACL_CONNECTED)
            addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED)
        }
        try {
            if (Build.VERSION.SDK_INT >= 33) activity.registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED)
            else activity.registerReceiver(receiver, filter)
            registered = true
        } catch (_: SecurityException) { }
    }

    fun stop() {
        if (!registered) return
        try { activity.unregisterReceiver(receiver) } catch (_: IllegalArgumentException) { }
        registered = false
    }
}
