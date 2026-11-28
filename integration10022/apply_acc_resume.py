from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
rep('    private var speedForeground = false','''    private var speedForeground = false
    private lateinit var bidAcc: BidAccResume''')
rep('        super.onResume()','''        super.onResume()
        if (::bidAcc.isInitialized) bidAcc.resumed()''')
rep('        super.onPause()', '''        if (::bidAcc.isInitialized) bidAcc.paused()
        super.onPause()''')
rep('        super.onDestroy()','''        if (::bidAcc.isInitialized) bidAcc.close()
        super.onDestroy()''')
rep('        webView.loadUrl("file:///android_asset/index.html")','''        bidAcc = BidAccResume(this)
        bidAcc.start()
        if (intent.hasCategory(Intent.CATEGORY_HOME)) bidAcc.homeIntent()
        webView.loadUrl("file:///android_asset/index.html")''')
rep('    override fun onLowMemory() {','''    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        enterFullscreen()
        if (::bidAcc.isInitialized && intent.hasCategory(Intent.CATEGORY_HOME)) bidAcc.homeIntent()
    }

    override fun onLowMemory() {''')
rep('    inner class Bridge {', '''    inner class Bridge {
        @JavascriptInterface
        fun openHomeSettings() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus()) return@runOnUiThread
            try {
                startActivity(Intent(android.provider.Settings.ACTION_HOME_SETTINGS))
            } catch (_: Exception) {
                android.widget.Toast.makeText(this@MainActivity, "Selector HOME indisponibil pe acest firmware", android.widget.Toast.LENGTH_LONG).show()
            }
        }

        @JavascriptInterface
        fun openQfReceptionTest() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus()) return@runOnUiThread
            try {
                startActivity(Intent(this@MainActivity, BidCanProbeActivity::class.java))
            } catch (_: Exception) {
                android.widget.Toast.makeText(this@MainActivity, "Diagnostic CANBUS indisponibil", android.widget.Toast.LENGTH_LONG).show()
            }
        }

        @JavascriptInterface
        fun standbyHistory(): String = if (::bidAcc.isInitialized) bidAcc.snapshot() else "[]"

        @JavascriptInterface
        fun showStandbyHistory() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus()) return@runOnUiThread
            val events = if (::bidAcc.isInitialized) bidAcc.snapshot() else "[]"
            val home = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
            val chosen = packageManager.resolveActivity(home, android.content.pm.PackageManager.MATCH_DEFAULT_ONLY)
            val chosenPackage = chosen?.activityInfo?.packageName
            val homeState = if (chosenPackage == packageName) "BID este HOME implicit"
                else if (chosenPackage == null || chosenPackage == "android") "HOME implicit neconfirmat"
                else "HOME rezolvat: " + chosenPackage
            val history = homeState + "\\n" + events
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("BID · diagnostic standby")
                .setMessage(history)
                .setNeutralButton("Copiază") { _, _ ->
                    val clipboard = getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                    clipboard.setPrimaryClip(android.content.ClipData.newPlainText("BID standby", history))
                }.setPositiveButton("Închide", null).show()
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/index.html'
s=p.read_text()
a='<button onclick="bidGeneralOpen()">Setări generale BID</button>'
assert s.count(a)==1
p.write_text(s.replace(a,a+'''<button onclick="if(window.BID)BID.showStandbyHistory()">Diagnostic standby</button><button onclick="if(window.BID)BID.openHomeSettings()">Alege launcher HOME</button><button onclick="if(window.BID)BID.openQfReceptionTest()">Test recepție CANBUS QF001</button>''',1))
p=root/'app/src/main/AndroidManifest.xml'
s=p.read_text()
a='android:name=".MainActivity" android:exported="true"'
assert s.count(a)==1
p.write_text(s.replace(a,a+' android:launchMode="singleTask"',1))
# Enable only the existing selectable HOME alias; never select it automatically.
p=root/'app/build.gradle.kts'
s=p.read_text()
a='manifestPlaceholders["bidHomeEnabled"] = "false"'
assert s.count(a)==1
p.write_text(s.replace(a,'manifestPlaceholders["bidHomeEnabled"] = "true"',1))

# Preserve the existing CANBUS probe and its authorization checks.
p=root/'app/src/main/java/ro/dj88bid/car/BidCanProbeActivity.kt'
s=p.read_text()
rep('    private val samples = ArrayDeque<String>()', '''    private val samples = ArrayDeque<String>()
    private val savedReport by lazy { getSharedPreferences("bid_can_report", Context.MODE_PRIVATE) }
    private var lastSavedAt = 0L
    private fun persistReport(force: Boolean = false) {
        val now = SystemClock.elapsedRealtime()
        if (!force && now - lastSavedAt < 5000L) return
        lastSavedAt = now
        savedReport.edit().putString("last_report", summary())
            .putLong("saved_wall_ms", System.currentTimeMillis()).apply()
    }''')
rep('        setContentView(root); render()', '''        setContentView(root); render()
        val previous = savedReport.getString("last_report", null)
        if (!previous.isNullOrEmpty()) {
            report.text = "Raport anterior salvat local; nu reprezintă date live.\\n" + previous
        }''')
rep('        running=true; deadline=SystemClock.elapsedRealtime()+120000', '''        running=true; deadline=SystemClock.elapsedRealtime()+120000
        lastSavedAt = 0L''')
rep('        running=false;++epoch;stage=reason;note(reason);ui.removeCallbacks(tick)', '''        running=false;++epoch;stage=reason;note(reason);ui.removeCallbacks(tick)
        persistReport(true)''')
rep('            render();ui.postDelayed(this,1000)', '''            render();persistReport();ui.postDelayed(this,1000)''')
rep('clipboard.setPrimaryClip(ClipData.newPlainText("BID CAN diagnostic",summary()))', '''clipboard.setPrimaryClip(ClipData.newPlainText("BID CAN diagnostic",report.text.toString()))''')
p.write_text(s)

# Decode only authenticated Binder samples with the reused BID experimental decoders.
# Older OEM field mappings remain candidates, never certified instrument values.
s=p.read_text()
rep('    private val samples = ArrayDeque<String>()', '''    private val samples = ArrayDeque<String>()
    private var candidate = "—"
    private fun decodeCandidate(bytes: ByteArray, isBody: Boolean): String {
        if (isBody) {
            val value = QfVehiclePacket.decode(bytes) ?: return "Format caroserie necunoscut"
            return "Candidat: km/h=" + (value.speed ?: "—") +
                "; RPM=" + (value.rpm ?: "—") + "; combustibil brut scalat=" + (value.fuel ?: "—") +
                "; kilometraj=" + (value.odometer ?: "—") + "; consum=" + (value.consumption ?: "—")
        }
        val mask = QfCabinPacket.doors(bytes) ?: return "Format uși necunoscut"
        return "Candidat mască uși: " + mask
    }''')
rep('        notes.clear();samples.clear();bodyCount=0;doorCount=0;lastBody=0;lastDoor=0', '''        candidate="—"
        notes.clear();samples.clear();bodyCount=0;doorCount=0;lastBody=0;lastDoor=0''')
rep('                        val item=(if(isBody)', '''                        candidate=decodeCandidate(bytes,isBody)
                        val item=(if(isBody)''')
rep('            appendLine("Etapă: $phase")', '''            appendLine("Etapă: $phase")
            appendLine("Decodare experimentală ultim mesaj (mapare OEM mai veche, nevalidată): " + candidate)''')
rep('Nicio valoare interpretată sau simulată. Nicio inițializare cu acreditări OEM.', 'Candidați din mesaje recepționate; nicio valoare simulată. Nicio inițializare cu acreditări OEM.')
p.write_text(s)

# Keep separate candidate channels so a door message cannot erase body evidence.
s=p.read_text()
rep('    private var candidate = "—"', '''    private var bodyCandidate = "—"
    private var doorCandidate = "—"''')
rep('        candidate="—"', '''        bodyCandidate="—";doorCandidate="—"''')
rep('                        candidate=decodeCandidate(bytes,isBody)', '''                        if (isBody) bodyCandidate=decodeCandidate(bytes,true)
                        else doorCandidate=decodeCandidate(bytes,false)''')
rep('            appendLine("Decodare experimentală ultim mesaj (mapare OEM mai veche, nevalidată): " + candidate)', '''            appendLine("Decodare experimentală (mapare OEM mai veche, nevalidată):")
            appendLine("Caroserie: " + if (running && lastBody>0L && now-lastBody<=5000L) bodyCandidate else "— · fără date recente")
            appendLine("Uși: " + if (running && lastDoor>0L && now-lastDoor<=30000L) doorCandidate else "— · fără date recente")
            appendLine("Ultimul candidat caroserie (istoric): " + bodyCandidate)
            appendLine("Ultimul candidat uși (istoric): " + doorCandidate)''')
p.write_text(s)

# Include read-only OEM sharing configuration in the existing reception report.
s=p.read_text()
rep('    private fun summary():String{', '''    private fun shareFlag(suffix: String): String {
        return try {
            when(android.provider.Settings.Global.getString(contentResolver, packageName + suffix)) {
                "1" -> "activ"
                "0" -> "inactiv"
                null -> "absent"
                else -> "necunoscut"
            }
        } catch (_: Exception) { "inaccesibil" }
    }
    private fun summary():String{''')
rep('            appendLine("Etapă: $phase")', '''            appendLine("Etapă: $phase")
            appendLine("Partajare OEM (citire, nu dovadă de recepție): caroserie=" +
                shareFlag("KeyShareCarbodyState") + "; uși=" + shareFlag("KeyShareDoorWindow") +
                "; climatizare=" + shareFlag("KeyShareAcState") + "; radar=" + shareFlag("KeyShareRadarState"))''')
rep('"; kilometraj=" + (value.odometer ?: "—") + "; consum=" + (value.consumption ?: "—")', '''"; kilometraj=" + (value.odometer ?: "—") + "; consum=" + (value.consumption ?: "—") +
                "; biți experimentali: frână=" + (value.parkingBrake ?: "—") +
                "; centură=" + (value.driverBeltUnfastened ?: "—") +
                "; lichid=" + (value.washerFlag ?: "—")''')
p.write_text(s)

# Foreground-only passive receiver for the already audited OEM broadcast format.
# Broadcast sender is not authenticated: never use these candidates for safety alerts.
p=root/'app/src/main/java/ro/dj88bid/car/BidPassiveCan.kt'
assert not p.exists()
p.write_text('''package ro.dj88bid.car

import android.app.Activity
import android.content.*
import android.os.Build
import android.os.SystemClock
import org.json.JSONObject

class BidPassiveCan(private val activity: Activity) {
    private val values = mutableMapOf<String, Pair<Long, JSONObject>>()
    private var active = false
    private var count = 0L
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (!active) return
            try {
                val now = SystemClock.elapsedRealtime()
                when (intent.action) {
                    "com.qf.vehicle.action.DATA_SHARE" -> {
                        val p = intent.getByteArrayExtra("extra_DATA_SHARE") ?: return
                        if (p.size < 2 || p.size > 79 || (p[0].toInt() and 255) != 46) return
                        val type = p[1].toInt() and 255
                        val o = JSONObject()
                        val key = when (type) {
                            2 -> {
                                val v = QfVehiclePacket.decode(p)
                                if (v == null) { values.remove("body"); return }
                                o.put("speed",v.speed ?: JSONObject.NULL)
                                o.put("rpm",v.rpm ?: JSONObject.NULL)
                                o.put("fuelRawScaled",v.fuel ?: JSONObject.NULL)
                                o.put("odometer",v.odometer ?: JSONObject.NULL)
                                "body"
                            }
                            1 -> {
                                val v = QfCabinPacket.climate(p)
                                if (v == null) { values.remove("climate"); return }
                                o.put("left",v.left ?: JSONObject.NULL).put("right",v.right ?: JSONObject.NULL)
                                "climate"
                            }
                            3 -> {
                                val v = QfCabinPacket.doors(p)
                                if (v == null) { values.remove("doors"); return }
                                o.put("mask",v); "doors"
                            }
                            4 -> {
                                val v = QfRadarPacket.levels(p)
                                if (v == null) { values.remove("radar"); return }
                                val a = org.json.JSONArray()
                                v.forEach { a.put(it ?: JSONObject.NULL) }
                                o.put("levels",a); "radar"
                            }
                            else -> return
                        }
                        values[key] = Pair(now,o)
                    }
                    "com.qf.vehicle.action.TEMP_STRING" -> {
                        val v = QfOutsideTemperature.parse(intent.getStringExtra("extra_string"))
                        if (v == null) { values.remove("temperature"); return }
                        values["temperature"] = Pair(now,JSONObject().put("celsius",v))
                    }
                    else -> return
                }
                count++
            } catch (_: RuntimeException) {}
        }
    }
    fun start() {
        if (active) return
        values.clear()
        val f = IntentFilter("com.qf.vehicle.action.DATA_SHARE")
        f.addAction("com.qf.vehicle.action.TEMP_STRING")
        try {
            if (Build.VERSION.SDK_INT >= 33) activity.registerReceiver(receiver,f,Context.RECEIVER_EXPORTED)
            else activity.registerReceiver(receiver,f)
            active = true
        } catch (_: RuntimeException) { active = false }
    }
    fun stop() {
        if (active) try { activity.unregisterReceiver(receiver) } catch (_: RuntimeException) {}
        active = false
        values.clear()
    }
    fun snapshot(): String {
        val now = SystemClock.elapsedRealtime()
        val o = JSONObject().put("verified",false).put("active",active).put("messages",count)
        for ((key,entry) in values) {
            val ttl = when(key) { "temperature" -> 120000L; "doors","climate" -> 30000L; else -> 5000L }
            if (active && now-entry.first in 0L..ttl) o.put(key,entry.second)
        }
        return o.toString()
    }
}
''')
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    private lateinit var bidAcc: BidAccResume', '''    private lateinit var bidAcc: BidAccResume
    private val passiveCan by lazy { BidPassiveCan(this) }''')
rep('        if (::bidAcc.isInitialized) bidAcc.resumed()', '''        if (::bidAcc.isInitialized) bidAcc.resumed()
        passiveCan.start()''')
rep('        if (::bidAcc.isInitialized) bidAcc.paused()', '''        passiveCan.stop()
        if (::bidAcc.isInitialized) bidAcc.paused()''')
rep('        if (::bidAcc.isInitialized) bidAcc.close()', '''        passiveCan.stop()
        if (::bidAcc.isInitialized) bidAcc.close()''')
rep('        fun standbyHistory(): String', '''        fun passiveCanReport() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus()) return@runOnUiThread
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("CANBUS pasiv · candidați nevalidați")
                .setMessage(passiveCan.snapshot())
                .setPositiveButton("Închide",null).show()
        }

        @JavascriptInterface
        fun standbyHistory(): String''')
p.write_text(s)
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep('>Test recepție CANBUS QF001</button>', '>Test recepție CANBUS QF001</button><button onclick="if(window.BID)BID.passiveCanReport()">Date CANBUS pasive</button>')
p.write_text(s)

# Complete the passive candidate set and refresh the existing report in place.
p=root/'app/src/main/java/ro/dj88bid/car/BidPassiveCan.kt'
s=p.read_text()
rep('                                o.put("odometer",v.odometer ?: JSONObject.NULL)', '''                                o.put("odometer",v.odometer ?: JSONObject.NULL)
                                o.put("consumption",v.consumption ?: JSONObject.NULL)
                                o.put("parkingBrakeCandidate",v.parkingBrake ?: JSONObject.NULL)
                                o.put("driverBeltCandidate",v.driverBeltUnfastened ?: JSONObject.NULL)
                                o.put("washerCandidate",v.washerFlag ?: JSONObject.NULL)''')
rep('                                o.put("left",v.left ?: JSONObject.NULL).put("right",v.right ?: JSONObject.NULL)', '''                                o.put("left",v.left ?: JSONObject.NULL).put("right",v.right ?: JSONObject.NULL)
                                o.put("power",v.power).put("ac",v.ac).put("auto",v.auto)
                                o.put("recirculation",v.recirculation).put("dual",v.dual)
                                o.put("numericUnitVerified",false)''')
rep('                    "com.qf.vehicle.action.TEMP_STRING" -> {', '''                    "com.qf.vehicle.action.swa" -> {
                        val angle = intent.getIntExtra("extra_angle",Int.MIN_VALUE)
                        if (angle == Int.MIN_VALUE || kotlin.math.abs(angle.toLong()) > 1000000L) {
                            values.remove("steering"); return
                        }
                        val rate = intent.getFloatExtra("extra_rate",Float.NaN)
                        values["steering"] = Pair(now,JSONObject().put("rawAngle",angle)
                            .put("rawRate",if(rate.isFinite()) rate else JSONObject.NULL))
                    }
                    "com.qf.action.BACKCAR_START", "com.qf.action.BACKCAR_STOP" -> {
                        values["reverseEvent"] = Pair(now,JSONObject()
                            .put("start",intent.action=="com.qf.action.BACKCAR_START"))
                    }
                    "com.qf.vehicle.action.TEMP_STRING" -> {''')
rep('        f.addAction("com.qf.vehicle.action.TEMP_STRING")', '''        f.addAction("com.qf.vehicle.action.TEMP_STRING")
        f.addAction("com.qf.vehicle.action.swa")
        f.addAction("com.qf.action.BACKCAR_START")
        f.addAction("com.qf.action.BACKCAR_STOP")''')
p.write_text(s)
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('''            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("CANBUS pasiv · candidați nevalidați")
                .setMessage(passiveCan.snapshot())
                .setPositiveButton("Închide",null).show()''', '''            fun formatted(): String = try {
                org.json.JSONObject(passiveCan.snapshot()).toString(2)
            } catch (_: Exception) { "Date indisponibile" }
            val dialog = android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("CANBUS pasiv · candidați nevalidați")
                .setMessage(formatted())
                .setPositiveButton("Închide",null).create()
            val handler = android.os.Handler(android.os.Looper.getMainLooper())
            val refresh = object : Runnable {
                override fun run() {
                    if (!dialog.isShowing || isFinishing || isDestroyed) return
                    dialog.setMessage(formatted())
                    handler.postDelayed(this,1000L)
                }
            }
            dialog.setOnDismissListener { handler.removeCallbacks(refresh) }
            dialog.show()
            handler.post(refresh)''')
p.write_text(s)

# Provide explicit source, age and confidence for the existing live report.
p=root/'app/src/main/java/ro/dj88bid/car/BidPassiveCan.kt'
s=p.read_text()
rep('    private var count = 0L', '''    private var count = 0L
    private var registrationError = ""
    private var oemVersion = "necunoscut"''')
rep('        values.clear()\n        val f = IntentFilter', '''        values.clear()
        registrationError = ""
        oemVersion = try {
            activity.packageManager.getPackageInfo("com.qf.vehicle",0).versionName ?: "necunoscut"
        } catch (_: Exception) { "indisponibil" }
        val f = IntentFilter''')
rep('        } catch (_: RuntimeException) { active = false }', '''        } catch (e: RuntimeException) {
            active = false
            registrationError = e.javaClass.simpleName
        }''')
rep('        val o = JSONObject().put("verified",false).put("active",active).put("messages",count)', '''        val o = JSONObject().put("verified",false).put("active",active).put("messages",count)
            .put("source","OEM broadcast; sender not authenticated")
            .put("oemVersion",oemVersion).put("registrationError",registrationError)
        val status = JSONObject()
        o.put("channels",status)''')
rep('        for ((key,entry) in values) {', '''        for (key in listOf("body","climate","doors","radar","temperature","steering","reverseEvent")) {
            val entry = values[key]
            if (entry == null) {
                status.put(key,JSONObject().put("fresh",false).put("ageMs",JSONObject.NULL))
                continue
            }''')
rep('            if (active && now-entry.first in 0L..ttl) o.put(key,entry.second)', '''            val age = now-entry.first
            val fresh = active && age in 0L..ttl
            status.put(key,JSONObject().put("fresh",fresh).put("ageMs",age))
            if (fresh) o.put(key,entry.second)''')
p.write_text(s)

# Publish candidates to the existing CANBUS status surface, not certified instruments.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    private val passiveCan by lazy { BidPassiveCan(this) }', '''    private val passiveCan by lazy { BidPassiveCan(this) }
    private val canUiHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private val canUiRefresh = object : Runnable {
        override fun run() {
            if (isFinishing || isDestroyed) return
            if (webView.url == "file:///android_asset/index.html") {
                webView.evaluateJavascript("if(window.bidCanStatus)window.bidCanStatus(" + passiveCan.snapshot() + ")",null)
            }
            canUiHandler.postDelayed(this,1000L)
        }
    }''')
rep('        passiveCan.start()', '''        passiveCan.start()
        canUiHandler.removeCallbacks(canUiRefresh)
        canUiHandler.post(canUiRefresh)''')
rep('        passiveCan.stop()\n        if (::bidAcc.isInitialized) bidAcc.paused()', '''        canUiHandler.removeCallbacks(canUiRefresh)
        passiveCan.stop()
        if (::bidAcc.isInitialized) bidAcc.paused()''')
rep('        passiveCan.stop()\n        if (::bidAcc.isInitialized) bidAcc.close()', '''        canUiHandler.removeCallbacks(canUiRefresh)
        passiveCan.stop()
        if (::bidAcc.isInitialized) bidAcc.close()''')
p.write_text(s)
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep('</body>', '''<script>
window.bidCanStatus=function(v){
 const el=document.getElementById('climateWarning');
 if(!el)return;
 const recent=v&&v.active&&Object.values(v.channels||{}).some(c=>c.fresh===true);
 el.textContent=recent?'CANBUS: date experimentale':'CANBUS: fără date recente';
 el.title=recent?'Date nevalidate; vezi raportul CANBUS pasiv':'Recepție neconfirmată';
};
</script></body>''')
p.write_text(s)

# Harden native Google Maps input and lifecycle without replacing the existing SDK.
p=root/'app/src/main/java/ro/dj88bid/car/BidGoogleMap.kt'
s=p.read_text()
rep('slot.alpha=j.optDouble("alpha",1.0).coerceIn(0.35,1.0).toFloat()', '''val rawAlpha=j.optDouble("alpha",1.0)
            slot.alpha=if(rawAlpha.isFinite())rawAlpha.coerceIn(0.35,1.0).toFloat() else 1f''')
rep('val zoom=j.optDouble("zoom",16.0).coerceIn(3.0,20.0).toFloat()', '''val rawZoom=j.optDouble("zoom",16.0)
            val zoom=if(rawZoom.isFinite())rawZoom.coerceIn(3.0,20.0).toFloat() else 16f''')
rep('if(sig!=previous){slot.layoutParams', '''if(rect[2]<1||rect[3]<1){hide();return@runOnUiThread}
            if(sig!=previous){slot.layoutParams''')
rep('if(settings!=config){', '''if(settings!=config){
                loaded=false''')
p.write_text(s)

# Prevent group visibility controls from modifying locked group members indirectly.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("return !!e&&!e.locked&&supported===true&&['hideInnerLabel','hideInnerGraphic'].includes(k);",
    "return !!e&&!e.locked&&!e.group&&supported===true&&['hideInnerLabel','hideInnerGraphic'].includes(k);")
p.write_text(s)
t=root/'tests/editor10022/test_inner_visibility.js'
with t.open('a') as f:
 f.write("\na.equal(f({group:'g'},'hideInnerLabel',true),false);\n")
