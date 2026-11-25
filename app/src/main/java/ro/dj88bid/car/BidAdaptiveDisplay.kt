package ro.dj88bid.car

import android.app.Activity
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import org.json.JSONObject

/** Window only: never changes global brightness or writes OEM settings. */
internal class BidAdaptiveDisplay(private val activity: Activity) : SensorEventListener {
    private val manager = activity.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val sensor = manager?.getDefaultSensor(Sensor.TYPE_LIGHT)
    @Volatile private var lux: Float? = null
    @Volatile private var requestedMode: String = "system"
    @Volatile private var active = false
    @Volatile private var sensorRegistered = false
    fun start() {
        manager?.unregisterListener(this)
        sensorRegistered = false
        lux = null
        active = true
        apply(requestedMode)
        if (sensor != null) {
            try { sensorRegistered = manager?.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL) == true } catch (_: Exception) { sensorRegistered = false }
        }
    }
    fun stop() {
        manager?.unregisterListener(this)
        sensorRegistered = false
        lux = null
        active = false
        setWindowBrightness(-1f)
    }
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    override fun onSensorChanged(event: SensorEvent?) {
        val value = event?.values?.firstOrNull()
        if (active && sensorRegistered && value != null && value.isFinite() && value >= 0f) {
            lux = value
        }
    }
    fun snapshot(): JSONObject = JSONObject().apply {
        put("hasLightSensor", sensor != null)
        put("sensorRegistered", active && sensorRegistered)
        val value = if (active && sensorRegistered) lux else null
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
        requestedMode = mode
        if (active) setWindowBrightness(brightness)
    }
    private fun setWindowBrightness(brightness: Float) {
        activity.runOnUiThread {
            val attrs = activity.window.attributes
            if (attrs.screenBrightness != brightness) {
                attrs.screenBrightness = brightness
                activity.window.attributes = attrs
            }
        }
    }
}
