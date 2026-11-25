package ro.dj88bid.car

import android.app.Activity
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.SystemClock
import org.json.JSONObject

/** Window only: never changes global brightness or writes OEM settings. */
internal class BidAdaptiveDisplay(private val activity: Activity) : SensorEventListener {
    private val manager = activity.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val sensor = manager?.getDefaultSensor(Sensor.TYPE_LIGHT)
    @Volatile private var lux: Float? = null
    @Volatile private var lastReading: Long = 0
    fun start() {
        lux = null
        lastReading = 0
        if (sensor != null) {
            try { manager?.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL) } catch (_: Exception) {}
        }
    }
    fun stop() {
        manager?.unregisterListener(this)
        lux = null
        lastReading = 0
        apply("system")
    }
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    override fun onSensorChanged(event: SensorEvent?) {
        val value = event?.values?.firstOrNull()
        if (value != null && value.isFinite() && value >= 0f) {
            lux = value
            lastReading = SystemClock.elapsedRealtime()
        }
    }
    fun snapshot(): JSONObject = JSONObject().apply {
        put("hasLightSensor", sensor != null)
        val value = lux
        put("lux", if (value != null) value else JSONObject.NULL)
    }
    fun apply(mode: String) {
        val brightness = when (mode) {
            "sun" -> 1f
            "day" -> 0.75f
            "night" -> 0.25f
            "system" -> -1f
            else -> return
        }
        activity.runOnUiThread {
            val attrs = activity.window.attributes
            if (attrs.screenBrightness != brightness) {
                attrs.screenBrightness = brightness
                activity.window.attributes = attrs
            }
        }
    }
}
