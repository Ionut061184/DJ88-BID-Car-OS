package ro.dj88bid.car

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.content.Context
import android.net.wifi.WifiManager
import android.net.wifi.SupplicantState
import android.os.Build
import android.telephony.TelephonyManager
import android.telephony.CellInfoGsm
import android.telephony.CellInfoWcdma
import android.telephony.CellInfoLte
import android.telephony.CellInfoCdma
import android.telephony.CellInfoNr
import android.telephony.CellInfoTdscdma
import org.json.JSONObject

/** Read-only Android state. OEM Bluetooth modules and modems may expose different data. */
internal object BidConnectivity {
    @Suppress("DEPRECATION")
    fun snapshot(context: Context): JSONObject {
        val result = JSONObject()
        listOf("wifi", "wifiConnected", "wifiLevel", "wifiRx", "wifiTx",
            "bluetooth", "bluetoothConnected", "simPresent", "cellLevel", "networkGeneration")
            .forEach { result.put(it, JSONObject.NULL) }
        try {
            val wifi = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
            if (wifi != null) {
                result.put("wifi", wifi.isWifiEnabled)
                if (wifi.isWifiEnabled) {
                    val info = wifi.connectionInfo
                    if (info != null) {
                        val connected = info.supplicantState == SupplicantState.COMPLETED
                        result.put("wifiConnected", connected)
                        if (connected && info.rssi in -126..-1)
                            result.put("wifiLevel", WifiManager.calculateSignalLevel(info.rssi, 5))
                    }
                } else result.put("wifiConnected", false)
            }
        } catch (_: Exception) {}
        try {
            val adapter = BluetoothAdapter.getDefaultAdapter()
            if (adapter != null) {
                result.put("bluetooth", adapter.isEnabled)
                if (!adapter.isEnabled) result.put("bluetoothConnected", false)
                else {
                    val audio = listOf(BluetoothProfile.HEADSET, BluetoothProfile.A2DP)
                        .map { adapter.getProfileConnectionState(it) }
                    val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
                    val gatt = try { manager?.getConnectedDevices(BluetoothProfile.GATT) } catch (_: Exception) { null }
                    if (audio.any { it == BluetoothProfile.STATE_CONNECTED } || gatt?.isNotEmpty() == true)
                        result.put("bluetoothConnected", true)
                    else if (audio.all { it == BluetoothProfile.STATE_DISCONNECTED } && gatt != null)
                        result.put("bluetoothConnected", false)
                }
            }
        } catch (_: Exception) {}
        // No fabricated values when the vendor uses a separate Bluetooth or cellular module.
        result.put("bluetoothSource", "ANDROID_PROFILES")
        try {
            val tm = context.getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
            if (tm != null && context.packageManager.hasSystemFeature("android.hardware.telephony")) {
                when (tm.simState) {
                    TelephonyManager.SIM_STATE_ABSENT -> result.put("simPresent", false)
                    TelephonyManager.SIM_STATE_READY -> result.put("simPresent", true)
                }
                if (result.optBoolean("simPresent", false)) {
                    val registered = tm.allCellInfo?.filter { it.isRegistered }.orEmpty()
                    val levels = registered.mapNotNull { cell ->
                        when {
                            cell is CellInfoLte -> cell.cellSignalStrength.level
                            cell is CellInfoWcdma -> cell.cellSignalStrength.level
                            cell is CellInfoGsm -> cell.cellSignalStrength.level
                            cell is CellInfoCdma -> cell.cellSignalStrength.level
                            Build.VERSION.SDK_INT >= 29 && cell is CellInfoNr -> cell.cellSignalStrength.level
                            Build.VERSION.SDK_INT >= 29 && cell is CellInfoTdscdma -> cell.cellSignalStrength.level
                            else -> null
                        }
                    }.filter { it in 0..4 }
                    if (levels.isNotEmpty()) result.put("cellLevel", levels.maxOrNull())
                    val type = if (Build.VERSION.SDK_INT >= 24) tm.dataNetworkType else tm.networkType
                    val generation = when(type) {
                        1,2,4,7,11,16 -> "2G"
                        3,5,6,8,9,10,12,14,15,17 -> "3G"
                        13 -> "4G"
                        19 -> "4G+"
                        20 -> "5G"
                        else -> null
                    }
                    if (generation != null) result.put("networkGeneration", generation)
                }
            }
        } catch (_: Exception) {}
        // TrafficStats totals cannot distinguish Wi-Fi from other non-cellular interfaces.
        // wifiRx/wifiTx stay null until a trustworthy per-interface source is verified.
        return result
    }
}
