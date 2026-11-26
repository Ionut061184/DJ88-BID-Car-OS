"""Static lifecycle contract; runtime power/RAM consumption requires physical measurements."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
K=(ROOT/"app/src/main/java/ro/dj88bid/car/MainActivity.kt").read_text()
J=(ROOT/"app/src/main/assets/bid_qf_vehicle.js").read_text()
P=(ROOT/"app/src/main/java/ro/dj88bid/car/QfVehicleProbe.java").read_text()
class Lifecycle(unittest.TestCase):
    def test_foreground_and_cleanup(self):
        resume=K.split("override fun onResume()",1)[1].split("override fun onPause()",1)[0]
        pause=K.split("override fun onPause()",1)[1].split("override fun onDestroy()",1)[0]
        destroy=K.split("override fun onDestroy()",1)[1].split("override fun onRequestPermissionsResult",1)[0]
        for x in ["bidForeground = true","webView.onResume()","invalidateVoltageCache()"]: self.assertIn(x,resume)
        for x in ["bidForeground = false","cancelManualWeather()","webView.onPause()","gpsWeather.stop()","qfVehicleProbe.foregroundChanged(false)"]: self.assertIn(x,pause)
        for x in ["manualWeatherWorker.shutdownNow()","gpsWeather.close()","webView.destroy()","qfVehicleProbe.close()","removeJavascriptInterface(\"BID\")"]: self.assertIn(x,destroy)
    def test_explicit_bounded_audit(self):
        self.assertIn("qfVehicleProbe.foregroundChanged(true)",K)
        self.assertIn("if (bidForeground && ::qfVehicleProbe.isInitialized) qfVehicleProbe.beginAudit()",K)
        self.assertIn("postDelayed(auditTimeout,120000)",P)
        self.assertIn("else if(!auditActive)stop()",P)
        self.assertIn("if(!auditForeground)stop()",P)
        self.assertIn("auditHandler.removeCallbacks(auditTimeout);stop();",P)
        for k in ["auditBeforeValid","auditAwayValid","auditAfterValid"]:
            self.assertIn(k,P)
            self.assertIn(k,J)
    def test_system_research_export_contract(self):
        f=(ROOT/"app/src/main/java/ro/dj88bid/car/QfFirmwareExport.kt").read_text()
        for expected in ["ACTION_OPEN_DOCUMENT_TREE","PART_BYTES","SHA-256","Os.lstat","S_ISLNK","FLAG_UPDATED_SYSTEM_APP","completeFirmware", "cancelled.get()","deleteDocument"]:
            self.assertIn(expected,f)
        for forbidden in ["Runtime.getRuntime","ProcessBuilder","/dev/block","Settings.Global.put","getExternalStorageDirectory","WRITE_SECURE_SETTINGS"]:
            self.assertNotIn(forbidden,f)
        self.assertIn("firmwareExport.handleResult(requestCode, resultCode, data)",K)
        self.assertIn("firmwareExport.close()",K)
        self.assertIn("if (bidForeground && !isDestroyed) firmwareExport.open()",K)
        self.assertIn("qfExportSystemFiles",J)
    def test_no_global_pause_or_power_control(self):
        for x in ["pauseTimers()","PowerManager.goToSleep","PowerManager.wakeUp","android.permission.WAKE_LOCK"]:
            self.assertNotIn(x,K)
    def test_weather_and_voltage(self):
        self.assertIn("token == weatherGeneration",K)
        self.assertIn("manualWeatherTask?.cancel(true)",K)
        self.assertIn("now - voltageAt in 0L..999L",K)
        self.assertIn('put("reason", "background")',K)
        self.assertIn("if(!document.hidden){refresh();poll=setInterval(refresh,1000);}",J)
        self.assertIn("clearInterval(poll)",J)
if __name__=="__main__":unittest.main()
