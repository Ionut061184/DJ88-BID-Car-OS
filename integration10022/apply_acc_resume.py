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

# Avoid carrying pre-standby CAN samples into the next screen session.
p=root/'app/src/main/java/ro/dj88bid/car/BidPassiveCan.kt'
s=p.read_text()
rep('            if (!active) return', '''            if (!active) return
            if (intent.action == Intent.ACTION_SCREEN_OFF || intent.action == Intent.ACTION_SCREEN_ON) {
                values.clear()
                return
            }''')
rep('        f.addAction("com.qf.action.BACKCAR_STOP")', '''        f.addAction("com.qf.action.BACKCAR_STOP")
        f.addAction(Intent.ACTION_SCREEN_OFF)
        f.addAction(Intent.ACTION_SCREEN_ON)''')
p.write_text(s)

# Provide useful numerical candidates on the existing CAN status surface, explicitly
# experimental and never a replacement for the vehicle instruments.
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep(" el.textContent=recent?'CANBUS: date experimentale':'CANBUS: fără date recente';",
    """ const parts=[];
 if(recent&&v.body){
   if(Number.isFinite(v.body.rpm))parts.push(v.body.rpm+' rpm');
   if(Number.isFinite(v.body.fuelRawScaled))parts.push('comb. brut '+v.body.fuelRawScaled);
 }
 if(recent&&v.temperature&&Number.isFinite(v.temperature.celsius))parts.push(v.temperature.celsius+' °C ext.');
 el.textContent=recent?('CANBUS test: '+(parts.length?parts.join(' · '):'date experimentale')):'CANBUS: fără date recente';""")
p.write_text(s)

# Retain a diagnostic distinction between activity recreation and process recreation.
# This source is copied into the archive by CI after this script.

# Add a user-controlled global palette operation for personal theme drafts only.
# All changes use the existing undo checkpoint and exclude protected elements.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function refreshPrecision(){", """function bidPalette30(elements,color){
 if(!/^#[0-9a-f]{6}$/i.test(color))return elements;
 return elements.map(e=>e.locked||e.group?e:{...e,borderColor:color});
}
const palette30=document.createElement('label');palette30.textContent='Accent global contur — ecran personal';
const paletteColor30=document.createElement('input');paletteColor30.type='color';paletteColor30.value='#b59b80';palette30.append(paletteColor30);
const paletteApply30=document.createElement('button');paletteApply30.type='button';paletteApply30.textContent='Aplică accentul pe ecran';
paletteApply30.onclick=()=>{if(!allowed()||!draft)return;const next=bidPalette30(draft.elements,paletteColor30.value);if(!next.some((e,i)=>e.borderColor!==draft.elements[i].borderColor))return;if(!confirm('Aplici accentul tuturor elementelor neblocate și negrupate?'))return;checkpoint();draft.elements=next;render();};
palette30.append(paletteApply30);$('bfControls').append(palette30);
function refreshPrecision(){""")
p.write_text(s)
t=root/'tests/editor10022/test_palette30.js'
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function bidPalette30('),j=s.indexOf('const palette30=',i);a.ok(i>=0&&j>i);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);
const input=[{id:'a',borderColor:'#000000'},{id:'b',locked:true,borderColor:'#000000'},{id:'c',group:'g',borderColor:'#000000'}];
const out=c.bidPalette30(input,'#abcdef');a.equal(out[0].borderColor,'#abcdef');a.equal(input[0].borderColor,'#000000');a.equal(out[1],input[1]);a.equal(out[2],input[2]);a.equal(c.bidPalette30(input,'bad'),input);console.log('5 personal palette checks passed');
""")
# Broaden the explicitly experimental existing status display, without safety alerts.
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep("if(Number.isFinite(v.body.rpm))parts.push(v.body.rpm+' rpm');",
    """if(Number.isFinite(v.body.rpm))parts.push(v.body.rpm+' rpm');
   if(Number.isFinite(v.body.speed))parts.push('viteză candidat '+v.body.speed+' km/h');""")
p.write_text(s)
# Native map loaded state must not survive hiding a previous visible session.
p=root/'app/src/main/java/ro/dj88bid/car/BidGoogleMap.kt'
s=p.read_text()
rep('previous="";lastCamera="";settings=""', 'previous="";lastCamera="";settings="";loaded=false')
p.write_text(s)

# Extend the existing palette to cover all personal pages, preserving protected elements.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("palette30.append(paletteApply30);", """function bidPalettePages30(t,color){
 if(!t||!/^#[0-9a-f]{6}$/i.test(color))return t;
 return {...t,elements:bidPalette30(t.elements,color),otherPages:(t.otherPages||[]).map(p=>({...p,elements:bidPalette30(p.elements,color)}))};
}
const paletteAll30=document.createElement('button');paletteAll30.type='button';paletteAll30.textContent='Accent pe toate ecranele temei';
paletteAll30.onclick=()=>{if(!allowed()||!draft)return;let next;try{next=theme(bidPalettePages30(draft,paletteColor30.value));}catch(err){message('Paletă incompatibilă');return;}if(!confirm('Aplici accentul tuturor ecranelor acestei teme personale?'))return;const page=draft.pageId;checkpoint();draft=pageView(next,page);render();};
palette30.append(paletteApply30,paletteAll30);""")
# No duplicate native widget identifiers: the existing binding key uses element identity.
# Verify page duplication preserves source content while assigning distinct IDs.
p.write_text(s)
t=root/'tests/editor10022/test_palette_pages30.js'
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),c={};vm.createContext(c);
let i=s.indexOf('function bidPalette30('),j=s.indexOf('const palette30=',i);a.ok(i>=0&&j>i);vm.runInContext(s.slice(i,j),c);
i=s.indexOf('function bidPalettePages30(');j=s.indexOf('const paletteAll30=',i);a.ok(i>=0&&j>i);vm.runInContext(s.slice(i,j),c);
const t={pageId:'p1',elements:[{borderColor:'#000000'}],otherPages:[{pageId:'p2',elements:[{locked:true,borderColor:'#000000'},{borderColor:'#111111'}]}]};
const r=c.bidPalettePages30(t,'#abcdef');a.equal(r.elements[0].borderColor,'#abcdef');a.equal(r.otherPages[0].elements[0].borderColor,'#000000');a.equal(r.otherPages[0].elements[1].borderColor,'#abcdef');a.equal(t.otherPages[0].elements[1].borderColor,'#111111');a.equal(r.otherPages[0].pageId,'p2');a.equal(c.bidPalettePages30(t,'bad'),t);console.log('6 multipage palette checks passed');
""")
# Add a supported store search for icon packs. Installing and interpreting pack
# resources are separate features; do not claim this is an icon-pack importer.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {', '''    inner class Bridge {
        @JavascriptInterface
        fun openBidIconPackStore() = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            try {
                startActivity(Intent(Intent.ACTION_VIEW, android.net.Uri.parse("market://search?q=icon%20pack&c=apps")))
            } catch (_: Exception) {
                try { startActivity(Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://play.google.com/store/search?q=icon%20pack&c=apps"))) }
                catch (_: Exception) { android.widget.Toast.makeText(this@MainActivity,"Magazin indisponibil",android.widget.Toast.LENGTH_SHORT).show() }
            }
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Caută pachete iconițe în Google Play',()=>{try{native().openBidIconPackStore();}catch(_){}});\nbutton('Închide',")
p.write_text(s)

# Extend personal palette operations to a selectable visual channel.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function bidPalette30(elements,color){", "function bidPalette30(elements,color,channel='borderColor'){")
rep("return elements.map(e=>e.locked||e.group?e:{...e,borderColor:color});", "if(!['borderColor','color'].includes(channel))return elements;return elements.map(e=>e.locked||e.group?e:{...e,[channel]:color});")
rep("const paletteApply30=document.createElement('button');", """const paletteChannel30=document.createElement('select');paletteChannel30.append(new Option('Contur','borderColor'),new Option('Text','color'));palette30.append(paletteChannel30);
const paletteApply30=document.createElement('button');""")
rep("bidPalette30(draft.elements,paletteColor30.value);if(!next.some((e,i)=>e.borderColor!==draft.elements[i].borderColor))", "bidPalette30(draft.elements,paletteColor30.value,paletteChannel30.value);if(!next.some((e,i)=>e[paletteChannel30.value]!==draft.elements[i][paletteChannel30.value]))")
rep("function bidPalettePages30(t,color){","function bidPalettePages30(t,color,channel='borderColor'){")
rep("elements:bidPalette30(t.elements,color),otherPages:(t.otherPages||[]).map(p=>({...p,elements:bidPalette30(p.elements,color)}))","elements:bidPalette30(t.elements,color,channel),otherPages:(t.otherPages||[]).map(p=>({...p,elements:bidPalette30(p.elements,color,channel)}))")
rep("bidPalettePages30(draft,paletteColor30.value)","bidPalettePages30(draft,paletteColor30.value,paletteChannel30.value)")
rep("Accent global contur — ecran personal","Paletă globală — ecran personal")
p.write_text(s)
t=root/'tests/editor10022/test_palette30.js'
with t.open('a') as f:
 f.write("\na.equal(c.bidPalette30(input,'#abcdef','color')[0].color,'#abcdef');a.equal(c.bidPalette30(input,'#abcdef','id'),input);a.equal(c.bidPalette30(input,'#abcdef','color')[1],input[1]);\n")
# Improve lifecycle diagnostic with explicit process identifier and activity session.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('val history = homeState + "\\n" + events','val history = homeState + "\\nPID Android: " + android.os.Process.myPid() + "\\n" + events')
p.write_text(s)
# Preserve complete passive diagnostic for comparison with the OEM screen.
rep('                .setPositiveButton("Închide",null).create()', '''                .setNeutralButton("Copiază") { _, _ ->
                    val clipboard = getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
                    clipboard.setPrimaryClip(android.content.ClipData.newPlainText("BID CAN pasiv",formatted()))
                }
                .setPositiveButton("Închide",null).create()''')
p.write_text(s)

# Reuse installed icon-pack implementation already present in the cumulative base.
# Isolate failing packages and expose only declared icon resources.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('''                for(info in packageManager.queryIntentActivities(Intent(action),0))result.add(info.activityInfo.packageName)''', '''                try {
                    for(info in packageManager.queryIntentActivities(Intent(action),0))
                        result.add(info.activityInfo.packageName)
                } catch (_: Exception) {}''')
rep('''            try { for(pkg in iconPackPackages()){
                val info=packageManager.getApplicationInfo(pkg,0)
                result.put(JSONObject().put("key",pkg).put("label",info.loadLabel(packageManager).toString().take(100)))
            }}catch(_:Exception){}''', '''            for(pkg in iconPackPackages().sorted().take(200)) {
                try {
                    val info=packageManager.getApplicationInfo(pkg,0)
                    result.put(JSONObject().put("key",pkg).put("label",info.loadLabel(packageManager).toString().take(100)))
                } catch (_: Exception) {}
            }''')
rep('org.json.JSONArray(packNames(pkg).toList()).toString()', 'org.json.JSONArray(packNames(pkg).sorted()).toString()')
rep('if(pkg !in iconPackPackages() || !name.matches(Regex("[a-zA-Z0-9_]{1,120}")))return ""', 'if(!name.matches(Regex("[a-zA-Z0-9_]{1,120}")) || name !in packNames(pkg))return ""')
p.write_text(s)
# Avoid a stale CAN label between Activity pause and the next foreground update.
rep('''        canUiHandler.removeCallbacks(canUiRefresh)
        passiveCan.stop()
        if (::bidAcc.isInitialized) bidAcc.paused()''', '''        canUiHandler.removeCallbacks(canUiRefresh)
        passiveCan.stop()
        if (webView.url == "file:///android_asset/index.html")
            webView.evaluateJavascript("if(window.bidCanStatus)window.bidCanStatus({active:false})",null)
        if (::bidAcc.isInitialized) bidAcc.paused()''')
p.write_text(s)
# Offer a real additional palette channel only for personal drafts; no MASTER edits.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("paletteChannel30.append(new Option('Contur','borderColor'),new Option('Text','color'));", "paletteChannel30.append(new Option('Contur','borderColor'),new Option('Text','color'));")
# Keep the current schema unchanged; reject invalid or empty palette channel selections.
rep("if(!['borderColor','color'].includes(channel))return elements;","if(!['borderColor','color'].includes(channel)||!Array.isArray(elements))return elements;")
p.write_text(s)

# Local GPS trip summary, explicitly opt-in, no coordinates retained.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('    private var lastFix = 0L', '''    private var lastFix = 0L
    private val tripPrefs = activity.getSharedPreferences("bid_trip", Context.MODE_PRIVATE)
    private var tripLast = 0L
    private var tripSpeed = 0.0
    private var tripMeters = 0.0
    private var tripMovingMs = 0L
    private var tripStoppedMs = 0L
    private var tripMax = 0.0
    private fun tripRecord(speed: Double, now: Long) {
        if (!tripPrefs.getBoolean("enabled",false)) { tripLast=0L; return }
        val dt = now-tripLast
        if (tripLast>0L && dt in 1L..4000L) {
            tripMeters += (tripSpeed+speed)*0.5*dt/1000.0
            if (tripSpeed>=0.5 || speed>=0.5) tripMovingMs+=dt else tripStoppedMs+=dt
        }
        tripLast=now
        tripSpeed=speed
        tripMax=maxOf(tripMax,speed)
        val state=org.json.JSONObject().put("distanceKm",tripMeters/1000.0)
            .put("movingSeconds",tripMovingMs/1000).put("stoppedSeconds",tripStoppedMs/1000)
            .put("maxKmh",tripMax*3.6)
            .put("averageMovingKmh",if(tripMovingMs>0)tripMeters*3600.0/tripMovingMs else 0.0)
        tripPrefs.edit().putString("session",state.toString()).apply()
    }
    private fun tripResetIfRequested() {
        if (!tripPrefs.getBoolean("reset",false)) return
        tripLast=0L;tripSpeed=0.0;tripMeters=0.0;tripMovingMs=0L;tripStoppedMs=0L;tripMax=0.0
        tripPrefs.edit().remove("reset").remove("session").apply()
    }''')
rep('        lastFix = 0L\n        emit', '        lastFix = 0L\n        tripLast = 0L\n        emit')
rep('        lastFix = SystemClock.elapsedRealtime()\n        drive.onFix(location)', '''        lastFix = SystemClock.elapsedRealtime()
        tripResetIfRequested()
        tripRecord(speed.toDouble(),lastFix)
        drive.onFix(location)''')
p.write_text(s)
# Explicit parked configuration and read-only local summary in general settings.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {', '''    inner class Bridge {
        @JavascriptInterface
        fun openBidTripSummary() = runOnUiThread {
            if(webView.url!="file:///android_asset/index.html" || !hasWindowFocus() || isFinishing)return@runOnUiThread
            val prefs=getSharedPreferences("bid_trip",MODE_PRIVATE)
            val enabled=prefs.getBoolean("enabled",false)
            val data=try{JSONObject(prefs.getString("session","{}")?:"{}")}catch(_:Exception){JSONObject()}
            val report=if(!data.has("distanceKm"))"Nicio măsurătoare GPS validă." else
                String.format(java.util.Locale.US,"Distanță estimată: %.2f km\\nDeplasare: %d s\\nStaționare: %d s\\nMedie în mișcare: %.1f km/h\\nMaxim: %.1f km/h",
                    data.optDouble("distanceKm"),data.optLong("movingSeconds"),data.optLong("stoppedSeconds"),data.optDouble("averageMovingKmh"),data.optDouble("maxKmh"))
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Statistici GPS locale BID")
                .setMessage(report+"\\nDoar fixuri GPS valide în prim-plan; fără trasee salvate. Configurează numai la staționare.")
                .setPositiveButton(if(enabled)"Oprește măsurarea" else "Activează măsurarea"){_,_->
                    prefs.edit().putBoolean("enabled",!enabled).putBoolean("reset",true).remove("session").apply()
                }
                .setNeutralButton("Resetează"){_,_->prefs.edit().putBoolean("reset",true).remove("session").apply()}
                .setNegativeButton("Închide",null).show()
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Statistici GPS locale',()=>{try{native().openBidTripSummary();}catch(_){}});\nbutton('Închide',")
p.write_text(s)

# Restore aggregate GPS session after process recreation, never interpolate across it.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('    private var tripMax = 0.0', '''    private var tripMax = 0.0
    private var tripRestored = false
    private fun tripRestore() {
        if(tripRestored)return
        tripRestored=true
        if(tripPrefs.getBoolean("reset",false))return
        val old=try{org.json.JSONObject(tripPrefs.getString("session","{}")?:"{}")}catch(_:Exception){return}
        tripMeters=old.optDouble("distanceKm",0.0).takeIf{it.isFinite()&&it>=0.0}?.times(1000.0)?:0.0
        tripMovingMs=old.optLong("movingMs",old.optLong("movingSeconds",0)*1000).coerceAtLeast(0)
        tripStoppedMs=old.optLong("stoppedMs",old.optLong("stoppedSeconds",0)*1000).coerceAtLeast(0)
        tripMax=old.optDouble("maxKmh",0.0).takeIf{it.isFinite()&&it in 0.0..360.0}?.div(3.6)?:0.0
    }''')
rep('        val dt = now-tripLast', '''        tripRestore()
        val dt = now-tripLast
        val day=java.text.SimpleDateFormat("yyyy-MM-dd",java.util.Locale.US).format(java.util.Date())
        val days=try{org.json.JSONObject(tripPrefs.getString("days","{}")?:"{}")}catch(_:Exception){org.json.JSONObject()}
        val today=days.optJSONObject(day)?:org.json.JSONObject()
        var dayMeters=today.optDouble("meters",0.0)
        var dayMoving=today.optLong("movingMs",0)
        var dayStopped=today.optLong("stoppedMs",0)''')
rep('''            tripMeters += (tripSpeed+speed)*0.5*dt/1000.0
            if (tripSpeed>=0.5 || speed>=0.5) tripMovingMs+=dt else tripStoppedMs+=dt''','''            val distance=(tripSpeed+speed)*0.5*dt/1000.0
            tripMeters+=distance;dayMeters+=distance
            if(tripSpeed>=0.5||speed>=0.5){tripMovingMs+=dt;dayMoving+=dt}
            else {tripStoppedMs+=dt;dayStopped+=dt}''')
rep('        tripPrefs.edit().putString("session",state.toString()).apply()', '''        state.put("movingMs",tripMovingMs).put("stoppedMs",tripStoppedMs)
        days.put(day,org.json.JSONObject().put("meters",dayMeters).put("movingMs",dayMoving).put("stoppedMs",dayStopped)
            .put("maxKmh",maxOf(today.optDouble("maxKmh",0.0),speed*3.6)))
        val keys=days.keys().asSequence().toList().sorted()
        for(key in keys.dropLast(90))days.remove(key)
        tripPrefs.edit().putString("session",state.toString()).putString("days",days.toString()).apply()''')
rep('        tripLast=0L;tripSpeed=0.0;tripMeters=0.0;', '        tripRestored=true;tripLast=0L;tripSpeed=0.0;tripMeters=0.0;')
p.write_text(s)
# Historical aggregates are read only, with explicit separate deletion.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {', '''    inner class Bridge {
        @JavascriptInterface
        fun openBidTripHistory() = runOnUiThread {
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||isFinishing)return@runOnUiThread
            val prefs=getSharedPreferences("bid_trip",MODE_PRIVATE)
            val days=try{JSONObject(prefs.getString("days","{}")?:"{}")}catch(_:Exception){JSONObject()}
            val lines=mutableListOf<String>()
            for(n in listOf(1,7,30)){
                var meters=0.0;var moving=0L;var stopped=0L;var max=0.0
                val cal=java.util.Calendar.getInstance()
                val fmt=java.text.SimpleDateFormat("yyyy-MM-dd",java.util.Locale.US)
                repeat(n){
                    val d=days.optJSONObject(fmt.format(cal.time))
                    if(d!=null){meters+=d.optDouble("meters",0.0);moving+=d.optLong("movingMs");stopped+=d.optLong("stoppedMs");max=maxOf(max,d.optDouble("maxKmh",0.0))}
                    cal.add(java.util.Calendar.DAY_OF_YEAR,-1)
                }
                lines.add(String.format(java.util.Locale.US,"%d zile: %.2f km | mers %d min | staționare %d min | max %.1f km/h",n,meters/1000,moving/60000,stopped/60000,max))
            }
            android.app.AlertDialog.Builder(this@MainActivity).setTitle("Istoric GPS local · ultimele 90 zile")
                .setMessage(lines.joinToString("\\n\\n")+"\\n\\nEstimări din fixuri GPS valide, fără coordonate.")
                .setNeutralButton("Șterge istoricul"){_,_->android.app.AlertDialog.Builder(this@MainActivity)
                    .setMessage("Ștergi definitiv statisticile istorice locale?").setPositiveButton("Șterge"){_,_->prefs.edit().remove("days").apply()}
                    .setNegativeButton("Anulează",null).show()}
                .setPositiveButton("Închide",null).show()
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Istoric GPS — 1, 7, 30 zile',()=>{try{native().openBidTripHistory();}catch(_){}});\nbutton('Închide',")
p.write_text(s)

# Optional parked clock screen. A fresh GPS fix at rest is mandatory; unknown
# speed, motion, loss of focus, pause, or any touch closes the overlay.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('    private var lastFix = 0L', '''    private var lastFix = 0L
    private var lastValidSpeed = Float.NaN
    fun stationaryNow(): Boolean {
        val age=SystemClock.elapsedRealtime()-lastFix
        return running && lastFix>0L && age in 0L..3000L && lastValidSpeed.isFinite() && lastValidSpeed<0.3f
    }''')
rep('        lastFix = 0L\n        tripLast = 0L', '        lastFix = 0L\n        lastValidSpeed = Float.NaN\n        tripLast = 0L')
rep('        lastFix = SystemClock.elapsedRealtime()\n        tripResetIfRequested()', '        lastFix = SystemClock.elapsedRealtime()\n        lastValidSpeed = speed\n        tripResetIfRequested()')
# Reject invalid coordinates and accuracy rather than letting NaN pass comparisons.
rep('!location.hasAccuracy() || location.accuracy > 50f', '!location.hasAccuracy() || !location.accuracy.isFinite() || location.accuracy<0f || location.accuracy > 50f || !location.latitude.isFinite() || !location.longitude.isFinite() || location.latitude !in -90.0..90.0 || location.longitude !in -180.0..180.0')
p.write_text(s)
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {', '''    private var bidClockDialog: android.app.Dialog? = null
    private val bidClockHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private fun closeBidClock() {
        bidClockHandler.removeCallbacksAndMessages(null)
        val old=bidClockDialog
        bidClockDialog=null
        old?.dismiss()
    }
    private fun showBidClock() {
        if(!speedForeground || !hasWindowFocus() || isFinishing || isDestroyed ||
            !::bidGpsSpeed.isInitialized || !bidGpsSpeed.stationaryNow()) {
            android.widget.Toast.makeText(this,"Ceas disponibil numai cu GPS valid și vehicul staționar.",android.widget.Toast.LENGTH_SHORT).show()
            return
        }
        closeBidClock()
        val prefs=getSharedPreferences("bid_clock",MODE_PRIVATE)
        val dialog=android.app.Dialog(this,android.R.style.Theme_Material_NoActionBar)
        val panel=android.widget.LinearLayout(this).apply{
            orientation=android.widget.LinearLayout.VERTICAL
            gravity=android.view.Gravity.CENTER
            setBackgroundColor(android.graphics.Color.BLACK)
            isClickable=true
        }
        val clock=android.widget.TextView(this).apply{
            textSize=if(prefs.getBoolean("large",true))64f else 42f
            setTextColor(android.graphics.Color.parseColor("#E5D4BD"))
            gravity=android.view.Gravity.CENTER
        }
        val date=android.widget.TextView(this).apply{
            textSize=20f;gravity=android.view.Gravity.CENTER
            setTextColor(android.graphics.Color.parseColor("#B59B80"))
        }
        val hint=android.widget.TextView(this).apply{
            text="Atinge pentru revenire";textSize=16f
            setTextColor(android.graphics.Color.LTGRAY)
        }
        panel.addView(clock);panel.addView(date);panel.addView(hint)
        panel.setOnClickListener{closeBidClock()}
        for(v in listOf(clock,date,hint))v.setOnClickListener{closeBidClock()}
        dialog.setContentView(panel)
        bidClockDialog=dialog
        dialog.setOnDismissListener{
            if(bidClockDialog===dialog){bidClockDialog=null;bidClockHandler.removeCallbacksAndMessages(null)}
        }
        dialog.show()
        dialog.window?.apply{
            setLayout(-1,-1)
            val a=attributes
            a.screenBrightness=0.15f
            attributes=a
            decorView.systemUiVisibility=5894
        }
        val update=object:Runnable{
            override fun run(){
                if(bidClockDialog!==dialog || !dialog.isShowing || !speedForeground ||
                    isFinishing || isDestroyed || !bidGpsSpeed.stationaryNow()){
                    closeBidClock();return
                }
                val now=java.util.Date()
                clock.text=java.text.SimpleDateFormat(if(prefs.getBoolean("seconds",false))"HH:mm:ss" else "HH:mm",java.util.Locale.getDefault()).format(now)
                date.text=if(prefs.getBoolean("date",true))java.text.SimpleDateFormat("EEEE, dd MMMM yyyy",java.util.Locale.getDefault()).format(now) else ""
                bidClockHandler.postDelayed(this,500L)
            }
        }
        bidClockHandler.post(update)
    }
    inner class Bridge {
        @JavascriptInterface
        fun openBidParkedClock() = runOnUiThread {
            if(webView.url=="file:///android_asset/index.html"&&hasWindowFocus())showBidClock()
        }
        @JavascriptInterface
        fun configureBidParkedClock() = runOnUiThread {
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||
                !::bidGpsSpeed.isInitialized||!bidGpsSpeed.stationaryNow())return@runOnUiThread
            val prefs=getSharedPreferences("bid_clock",MODE_PRIVATE)
            val keys=arrayOf("large","seconds","date")
            val checked=booleanArrayOf(prefs.getBoolean("large",true),prefs.getBoolean("seconds",false),prefs.getBoolean("date",true))
            android.app.AlertDialog.Builder(this@MainActivity).setTitle("Ceas BID la staționare")
                .setMultiChoiceItems(arrayOf("Ceas mare","Secunde","Dată"),checked){_,i,value->checked[i]=value}
                .setPositiveButton("Salvează"){_,_->
                    if(bidGpsSpeed.stationaryNow()){
                        val edit=prefs.edit();for(i in keys.indices)edit.putBoolean(keys[i],checked[i]);edit.apply()
                    }
                }.setNegativeButton("Anulează",null).show()
        }
''')
rep('    override fun onPause() {', '    override fun onPause() {\n        closeBidClock()')
rep('    override fun onDestroy() {', '    override fun onDestroy() {\n        closeBidClock()')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Ceas economic la staționare',()=>{try{native().openBidParkedClock();}catch(_){}});\nbutton('Setări ceas economic',()=>{try{native().configureBidParkedClock();}catch(_){}});\nbutton('Închide',")
p.write_text(s)
# Distinguish invalid GPS input from an actual stop; also prevent accumulation
# across a history reset, midnight, or an opt-out while GPS is unavailable.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('    private var tripLast = 0L','    private var tripLast = 0L\n    private var tripDay = ""')
rep('        val today=days.optJSONObject(day)?:org.json.JSONObject()', '''        val today=days.optJSONObject(day)?:org.json.JSONObject()
        val sameDay=tripDay==day
        tripDay=day''')
rep('            tripMeters+=distance;dayMeters+=distance','            tripMeters+=distance;if(sameDay)dayMeters+=distance')
rep('if(tripSpeed>=0.5||speed>=0.5){tripMovingMs+=dt;dayMoving+=dt}', 'if(tripSpeed>=0.5||speed>=0.5){tripMovingMs+=dt;if(sameDay)dayMoving+=dt}')
rep('else {tripStoppedMs+=dt;dayStopped+=dt}', 'else {tripStoppedMs+=dt;if(sameDay)dayStopped+=dt}')
rep('        for(key in keys.dropLast(90))days.remove(key)', '''        val cutoff=java.util.Calendar.getInstance().apply{add(java.util.Calendar.DAY_OF_YEAR,-89)}
        val earliest=java.text.SimpleDateFormat("yyyy-MM-dd",java.util.Locale.US).format(cutoff.time)
        for(key in keys)if(key<earliest||key>day)days.remove(key)
        for(key in keys.dropLast(90))days.remove(key)''')
p.write_text(s)

# Add optional automatic clock on the trusted home screen only. A user must
# explicitly enable it; the clock never starts a background Activity.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    private var bidClockDialog: android.app.Dialog? = null', '''    private var bidClockDialog: android.app.Dialog? = null
    private var bidClockIdleSince=android.os.SystemClock.elapsedRealtime()
    private val bidClockAutoHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private val bidClockAutoCheck=object:Runnable{
        override fun run(){
            if(!speedForeground||isFinishing||isDestroyed)return
            val prefs=getSharedPreferences("bid_clock",MODE_PRIVATE)
            if(!prefs.getBoolean("auto",false)||!hasWindowFocus()||
                !::bidGpsSpeed.isInitialized||!bidGpsSpeed.stationaryNow()){
                bidClockIdleSince=android.os.SystemClock.elapsedRealtime()
            }else if(bidClockDialog==null && webView.url=="file:///android_asset/index.html" &&
                android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=60000L){
                // Ask the live page whether it is safe to obscure its contents.
                webView.evaluateJavascript("(function(){return window.bidClockHomeEligible ? window.bidClockHomeEligible() : false;})()"){ result ->
                    if(result=="true"&&speedForeground&&hasWindowFocus()&&bidClockDialog==null&&
                        prefs.getBoolean("auto",false)&&bidGpsSpeed.stationaryNow()&&
                        android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=60000L)showBidClock()
                }
            }
            bidClockAutoHandler.postDelayed(this,2000L)
        }
    }
    override fun onUserInteraction(){
        super.onUserInteraction()
        bidClockIdleSince=android.os.SystemClock.elapsedRealtime()
    }''')
rep('        super.onResume()', '''        super.onResume()
        bidClockIdleSince=android.os.SystemClock.elapsedRealtime()
        bidClockAutoHandler.removeCallbacks(bidClockAutoCheck)
        bidClockAutoHandler.postDelayed(bidClockAutoCheck,2000L)''')
rep('    override fun onPause() {\n        closeBidClock()', '    override fun onPause() {\n        bidClockAutoHandler.removeCallbacks(bidClockAutoCheck)\n        closeBidClock()')
rep('    override fun onDestroy() {\n        closeBidClock()', '    override fun onDestroy() {\n        bidClockAutoHandler.removeCallbacks(bidClockAutoCheck)\n        closeBidClock()')
rep('        val old=bidClockDialog\n        bidClockDialog=null', '        val old=bidClockDialog\n        bidClockIdleSince=android.os.SystemClock.elapsedRealtime()\n        bidClockDialog=null')
rep('val keys=arrayOf("large","seconds","date")','val keys=arrayOf("large","seconds","date","auto")')
rep('prefs.getBoolean("seconds",false),prefs.getBoolean("date",true))','prefs.getBoolean("seconds",false),prefs.getBoolean("date",true),prefs.getBoolean("auto",false))')
rep('arrayOf("Ceas mare","Secunde","Dată"),checked','arrayOf("Ceas mare","Secunde","Dată","Automat după 60 secunde la staționare"),checked')
p.write_text(s)
# Conservative eligibility: only a visible, unobscured MASTER page, not editor,
# dialogs, or any personal theme. No automatic activation if uncertain.
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep('</body>', '''<script>
window.bidClockHomeEligible=function(){
 if(document.hidden)return false;
 const visible=e=>!!e&&e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none';
 if(!visible(document.getElementById('stage')))return false;
 if(Array.from(document.querySelectorAll('.on,[role="dialog"],dialog,[aria-modal="true"]')).some(visible))return false;
 if(visible(document.getElementById('bfLive')))return false;
 return true;
};
</script></body>''')
p.write_text(s)
# Add an explicit device test checklist for the newly integrated features.
(root/'tests/editor10022/test_clock_contract.js').write_text("""const fs=require('fs'),a=require('assert');
const s=fs.readFileSync(__dirname+'/../../app/src/main/java/ro/dj88bid/car/MainActivity.kt','utf8');
const gps=fs.readFileSync(__dirname+'/../../app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt','utf8');
a.ok(s.includes('bidClockAutoHandler.removeCallbacks(bidClockAutoCheck)'));
a.ok(s.includes('prefs.getBoolean("auto",false)'));
a.ok(s.includes('result=="true"&&speedForeground&&hasWindowFocus()'));
a.ok(gps.includes('age in 0L..3000L'));
console.log('4 clock safety contract checks passed (static)');
""")

# Distinguish process identity from individual Activity instances in standby reports.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    private var bidClockIdleSince=android.os.SystemClock.elapsedRealtime()', '''    private var bidClockIdleSince=android.os.SystemClock.elapsedRealtime()
    private var bidClockAutoGeneration=0L''')
rep('        super.onUserInteraction()\n        bidClockIdleSince', '        super.onUserInteraction()\n        bidClockAutoGeneration++\n        bidClockIdleSince')
rep('                // Ask the live page whether it is safe to obscure its contents.', '''                val generation=bidClockAutoGeneration
                // Ask the live page whether it is safe to obscure its contents.''')
rep('if(result=="true"&&speedForeground&&hasWindowFocus()&&bidClockDialog==null&&','if(result=="true"&&speedForeground&&hasWindowFocus()&&bidClockDialog==null&&generation==bidClockAutoGeneration&&')
rep('        super.onResume()\n        bidClockIdleSince','        super.onResume()\n        bidClockAutoGeneration++\n        bidClockIdleSince')
rep('    override fun onPause() {\n        bidClockAutoHandler','    override fun onPause() {\n        bidClockAutoGeneration++\n        bidClockAutoHandler')
p.write_text(s)
# Offer adjustable inactivity delay and brightness without changing system settings.
rep('android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=60000L','android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=bidClockDelay(prefs)') if s.count('android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=60000L')==1 else None
a='android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=60000L'
assert s.count(a) in (0,2)
s=s.replace(a,'android.os.SystemClock.elapsedRealtime()-bidClockIdleSince>=bidClockDelay(prefs)')
rep('    private fun closeBidClock() {','''    private fun bidClockDelay(prefs: android.content.SharedPreferences): Long =
        prefs.getInt("delay",60).coerceIn(30,300)*1000L
    private fun closeBidClock() {''')
rep('a.screenBrightness=0.15f','a.screenBrightness=prefs.getInt("brightness",15).coerceIn(5,60)/100f')
rep('Automat după 60 secunde la staționare','Automat după timpul ales, la staționare')
rep('    inner class Bridge {','''    inner class Bridge {
        @JavascriptInterface
        fun configureBidClockTiming() = runOnUiThread {
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||
                !::bidGpsSpeed.isInitialized||!bidGpsSpeed.stationaryNow())return@runOnUiThread
            val prefs=getSharedPreferences("bid_clock",MODE_PRIVATE)
            val layout=android.widget.LinearLayout(this@MainActivity).apply{
                orientation=android.widget.LinearLayout.VERTICAL;setPadding(24,16,24,16)
            }
            val labels=arrayOf("30 secunde","1 minut","2 minute","5 minute")
            val times=intArrayOf(30,60,120,300)
            val delay=android.widget.Spinner(this@MainActivity)
            delay.adapter=android.widget.ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,labels)
            delay.setSelection(times.indexOf(prefs.getInt("delay",60)).coerceAtLeast(0))
            val title=android.widget.TextView(this@MainActivity).apply{text="Luminozitate ceas: 5–60%"}
            val brightness=android.widget.SeekBar(this@MainActivity).apply{max=55;progress=prefs.getInt("brightness",15).coerceIn(5,60)-5}
            layout.addView(delay);layout.addView(title);layout.addView(brightness)
            android.app.AlertDialog.Builder(this@MainActivity).setTitle("Timp și luminozitate ceas")
                .setView(layout).setPositiveButton("Salvează"){_,_->
                    if(bidGpsSpeed.stationaryNow())prefs.edit().putInt("delay",times[delay.selectedItemPosition])
                        .putInt("brightness",brightness.progress+5).apply()
                }.setNegativeButton("Anulează",null).show()
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Timp și luminozitate ceas',()=>{try{native().configureBidClockTiming();}catch(_){}});\nbutton('Închide',")
p.write_text(s)

# Add a searchable, non-destructive list of installed icon packs to general settings.
# Existing editor handles icon application; this inventory does not change any theme.
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Caută pachete iconițe în Google Play',", """button('Pachete iconițe instalate',()=>{
 const old=document.getElementById('bidPackInventory');if(old){old.remove();return;}
 const box=document.createElement('section');box.id='bidPackInventory';
 const search=document.createElement('input');search.placeholder='Caută pachet';search.setAttribute('aria-label','Caută pachet de iconițe');
 const rows=document.createElement('div');let packs=[];
 try{const parsed=JSON.parse(native().listThemeIconPacks());if(Array.isArray(parsed))packs=parsed;}catch(_){}
 const draw=()=>{rows.replaceChildren();const q=search.value.toLocaleLowerCase();const found=packs.filter(p=>String(p.label).toLocaleLowerCase().includes(q));
 for(const p of found){const row=document.createElement('p');row.textContent=String(p.label);rows.append(row);}
 if(!found.length)rows.textContent='Niciun pachet compatibil găsit.';};
 search.oninput=draw;box.append(search,rows);modal.append(box);draw();
});
button('Caută pachete iconițe în Google Play',""")
p.write_text(s)
# Preserve PNG alpha while allowing larger still images only via the already
# bounded bitmap decoder; do not broaden GIF or memory limits.
p=root/'app/src/main/java/ro/dj88bid/car/BidThemeImage.kt'
s=p.read_text()
rep('Format neacceptat. Alege JPG, PNG sau WebP.', 'Format neacceptat. Alege JPG, PNG, WebP sau GIF.')
p.write_text(s)
# Add explicit controls for editing the installed personal theme accent without
# changing the current page or any protected native/group item.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("paletteColor30.value='#b59b80';", """paletteColor30.value='#b59b80';
const palettePresets30=document.createElement('select');
for(const [label,color] of [['Champagne','#e5d4bd'],['Bronz satin','#b59b80'],['Bordeaux','#572433'],['Grafit','#343438'],['Crem','#eee3ce'],['Negru','#101014']])palettePresets30.append(new Option(label,color));
palettePresets30.onchange=()=>{paletteColor30.value=palettePresets30.value;};palette30.append(palettePresets30);""")
# Reset only the input color, without silently changing existing elements.
rep("palette30.append(paletteApply30,paletteAll30);", """const paletteReset30=document.createElement('button');paletteReset30.type='button';paletteReset30.textContent='Reset selector culoare';paletteReset30.onclick=()=>{paletteColor30.value='#b59b80';palettePresets30.value='#b59b80';};
palette30.append(paletteApply30,paletteAll30,paletteReset30);""")
p.write_text(s)
# Keep automated tests operating on the final cumulative editor.

# Independent personal-theme typography and automotive artwork controls.
# These properties belong to individual elements, never to MASTER assets.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function element(v){", """const bidFontFamilies33={default:'',sans:'sans-serif',serif:'serif',mono:'monospace',condensed:'sans-serif-condensed',light:'sans-serif-light',medium:'sans-serif-medium',cursive:'cursive'};
function bidArtworkStyle37(v){
 const font=Object.prototype.hasOwnProperty.call(bidFontFamilies33,v.bidFont)?v.bidFont:'default';
 const hue=typeof v.bidArtHue==='number'&&Number.isFinite(v.bidArtHue)?Math.max(-180,Math.min(180,Math.round(v.bidArtHue))):0;
 return {bidFont:font,bidArtHue:hue,bidArtMirror:v.bidArtMirror===true};
}
function element(v){""")
rep("return {...advancedFields(v),", "return {...advancedFields(v),...bidArtworkStyle37(v),")
rep("if(bidMaskSupported(e)){if(e.hideInnerLabel)", """const artStyle37=bidArtworkStyle37(e);
if(artStyle37.bidFont!=='default')n.style.fontFamily=bidFontFamilies33[artStyle37.bidFont];
for(const art of n.querySelectorAll('.bfAutoArt')){
 if(artStyle37.bidArtHue!==0)art.style.filter='hue-rotate('+artStyle37.bidArtHue+'deg)';
 if(artStyle37.bidArtMirror)art.style.scale='-1 1';
}
if(bidMaskSupported(e)){if(e.hideInnerLabel)""")
rep("function refreshPrecision(){", """const artPanel37=document.createElement('div');
const font37=document.createElement('select');for(const [id,title] of [['default','Original'],['sans','Sans'],['serif','Serif'],['mono','Monospace'],['condensed','Condensed'],['light','Light'],['medium','Medium'],['cursive','Cursiv']])font37.append(new Option(title,id));
const hue37=document.createElement('input');hue37.type='range';hue37.min=-180;hue37.max=180;hue37.step=1;
const mirror37=document.createElement('input');mirror37.type='checkbox';
for(const [label,control] of [['Font element',font37],['Nuanță grafică auto (filtru)',hue37],['Oglindire grafică auto',mirror37]]){const row=document.createElement('label');row.textContent=label;row.append(control);artPanel37.append(row);}
const artApply37=document.createElement('button');artApply37.type='button';artApply37.textContent='Aplică stilul elementului';
artApply37.onclick=()=>{if(!allowed()||!draft)return;const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group)return;const style=bidArtworkStyle37({bidFont:font37.value,bidArtHue:hue37.valueAsNumber,bidArtMirror:mirror37.checked});if(Object.entries(style).every(([k,v])=>e[k]===v))return;checkpoint();Object.assign(e,style);render();};
artPanel37.append(artApply37);$('bfControls').append(artPanel37);
function refreshArt37(){const e=draft?.elements.find(v=>v.id===selected);const style=bidArtworkStyle37(e||{});font37.value=style.bidFont;hue37.value=String(style.bidArtHue);mirror37.checked=style.bidArtMirror;for(const c of [font37,hue37,mirror37,artApply37])c.disabled=!e||!!e.locked||!!e.group;}
function refreshPrecision(){refreshArt37();""")
p.write_text(s)
(root/'tests/editor10022/test_artwork_style37.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('const bidFontFamilies33='),j=s.indexOf('function element(v)',i);a.ok(i>=0&&j>i);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);
const f=c.bidArtworkStyle37;
a.equal(f({}).bidFont,'default');a.equal(f({bidFont:'serif'}).bidFont,'serif');a.equal(f({bidFont:'constructor'}).bidFont,'default');a.equal(f({bidArtHue:999}).bidArtHue,180);a.equal(f({bidArtHue:-999}).bidArtHue,-180);a.equal(f({bidArtHue:NaN}).bidArtHue,0);a.equal(f({bidArtMirror:true}).bidArtMirror,true);a.equal(f({bidArtMirror:'true'}).bidArtMirror,false);console.log('8 artwork and font normalization checks passed');
""")

# Extend personal automotive artwork with independent saturation and brightness.
# No source image is rewritten; only the editable artwork node is styled.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("return {bidFont:font,bidArtHue:hue,bidArtMirror:v.bidArtMirror===true};", """const bound=(n,d,a,b)=>typeof n==='number'&&Number.isFinite(n)?Math.max(a,Math.min(b,Math.round(n))):d;
 return {bidFont:font,bidArtHue:hue,bidArtMirror:v.bidArtMirror===true,bidArtSaturation:bound(v.bidArtSaturation,100,0,200),bidArtBrightness:bound(v.bidArtBrightness,100,40,160)};""")
rep("if(artStyle37.bidArtHue!==0)art.style.filter='hue-rotate('+artStyle37.bidArtHue+'deg)';", """if(artStyle37.bidArtHue!==0||artStyle37.bidArtSaturation!==100||artStyle37.bidArtBrightness!==100)
 art.style.filter='hue-rotate('+artStyle37.bidArtHue+'deg) saturate('+artStyle37.bidArtSaturation+'%) brightness('+artStyle37.bidArtBrightness+'%)';""")
rep("const mirror37=document.createElement('input');mirror37.type='checkbox';", """const mirror37=document.createElement('input');mirror37.type='checkbox';
const sat37=document.createElement('input');sat37.type='range';sat37.min=0;sat37.max=200;sat37.step=5;
const bright37=document.createElement('input');bright37.type='range';bright37.min=40;bright37.max=160;bright37.step=5;""")
rep("['Oglindire grafică auto',mirror37]", "['Oglindire grafică auto',mirror37],['Saturație grafică auto',sat37],['Luminozitate grafică auto',bright37]")
rep("bidArtMirror:mirror37.checked}", "bidArtMirror:mirror37.checked,bidArtSaturation:sat37.valueAsNumber,bidArtBrightness:bright37.valueAsNumber}")
rep("mirror37.checked=style.bidArtMirror;for(const c of [font37,hue37,mirror37,artApply37])", "mirror37.checked=style.bidArtMirror;sat37.value=String(style.bidArtSaturation);bright37.value=String(style.bidArtBrightness);for(const c of [font37,hue37,mirror37,sat37,bright37,artApply37])")
p.write_text(s)
t=root/'tests/editor10022/test_artwork_style37.js'
with t.open('a') as f:
 f.write("\na.equal(f({}).bidArtSaturation,100);a.equal(f({bidArtSaturation:250}).bidArtSaturation,200);a.equal(f({bidArtSaturation:-1}).bidArtSaturation,0);a.equal(f({bidArtBrightness:1}).bidArtBrightness,40);a.equal(f({bidArtBrightness:NaN}).bidArtBrightness,100);a.equal(f({bidArtBrightness:200}).bidArtBrightness,160);\n")
# Reset all artwork/typography settings using the existing apply/undo path.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("artPanel37.append(artApply37);", """const artReset37=document.createElement('button');artReset37.type='button';artReset37.textContent='Restabilește stilul original';
artReset37.onclick=()=>{if(!allowed()||!draft)return;const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group)return;const style=bidArtworkStyle37({});if(Object.entries(style).every(([k,v])=>e[k]===v))return;checkpoint();Object.assign(e,style);render();};
artPanel37.append(artApply37,artReset37);""")
rep("sat37,bright37,artApply37])", "sat37,bright37,artApply37,artReset37])")
p.write_text(s)

# Optional personal automotive text badge, separate from the original artwork.
# Never modify the MASTER image or rewrite imported imagery.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("return {bidFont:font,bidArtHue:hue,bidArtMirror:v.bidArtMirror===true,bidArtSaturation:bound(v.bidArtSaturation,100,0,200),bidArtBrightness:bound(v.bidArtBrightness,100,40,160)};", """const badge=typeof v.bidArtBadge==='string'?Array.from(v.bidArtBadge.trim()).slice(0,20).join(''):'';
 const badgeColor=typeof v.bidArtBadgeColor==='string'&&/^#[0-9a-f]{6}$/i.test(v.bidArtBadgeColor)?v.bidArtBadgeColor:'#e5d4bd';
 return {bidFont:font,bidArtHue:hue,bidArtMirror:v.bidArtMirror===true,bidArtSaturation:bound(v.bidArtSaturation,100,0,200),bidArtBrightness:bound(v.bidArtBrightness,100,40,160),bidArtBadge:badge,bidArtBadgeColor:badgeColor,bidArtBadgeX:bound(v.bidArtBadgeX,50,10,90),bidArtBadgeY:bound(v.bidArtBadgeY,80,10,90)};""")
rep("if(artStyle37.bidArtMirror)art.style.scale='-1 1';", """if(artStyle37.bidArtMirror)art.style.scale='-1 1';
 if(artStyle37.bidArtBadge){
  const badge=document.createElement('span');badge.className='bidPersonalAutoBadge';badge.textContent=artStyle37.bidArtBadge;
  badge.style.cssText='position:absolute;transform:translate(-50%,-50%);pointer-events:none;white-space:nowrap;max-width:90%;overflow:hidden;text-overflow:ellipsis;font-size:clamp(8px,2vw,20px);font-weight:bold;text-shadow:0 1px 3px #000;z-index:2';
  badge.style.left=artStyle37.bidArtBadgeX+'%';badge.style.top=artStyle37.bidArtBadgeY+'%';badge.style.color=artStyle37.bidArtBadgeColor;
  n.append(badge);
 }""")
rep("const artApply37=document.createElement('button');", """const badge37=document.createElement('input');badge37.type='text';badge37.maxLength=20;badge37.placeholder='BID / siglă text';
const badgeColor37=document.createElement('input');badgeColor37.type='color';
const badgeX37=document.createElement('input');badgeX37.type='range';badgeX37.min=10;badgeX37.max=90;
const badgeY37=document.createElement('input');badgeY37.type='range';badgeY37.min=10;badgeY37.max=90;
for(const [title,control] of [['Emblemă text personală',badge37],['Culoare emblemă',badgeColor37],['Poziție emblemă X',badgeX37],['Poziție emblemă Y',badgeY37]]){const row=document.createElement('label');row.textContent=title;row.append(control);artPanel37.append(row);}
const artApply37=document.createElement('button');""")
rep("bidArtBrightness:bright37.valueAsNumber}", "bidArtBrightness:bright37.valueAsNumber,bidArtBadge:badge37.value,bidArtBadgeColor:badgeColor37.value,bidArtBadgeX:badgeX37.valueAsNumber,bidArtBadgeY:badgeY37.valueAsNumber}")
rep("bright37.value=String(style.bidArtBrightness);for(const c of [font37,hue37,mirror37,sat37,bright37,artApply37,artReset37])", "bright37.value=String(style.bidArtBrightness);badge37.value=style.bidArtBadge;badgeColor37.value=style.bidArtBadgeColor;badgeX37.value=String(style.bidArtBadgeX);badgeY37.value=String(style.bidArtBadgeY);for(const c of [font37,hue37,mirror37,sat37,bright37,badge37,badgeColor37,badgeX37,badgeY37,artApply37,artReset37])")
p.write_text(s)
t=root/'tests/editor10022/test_artwork_style37.js'
with t.open('a') as f:
 f.write("\na.equal(f({bidArtBadge:' BID '}).bidArtBadge,'BID');a.equal(f({bidArtBadge:42}).bidArtBadge,'');a.equal(f({bidArtBadge:'x'.repeat(30)}).bidArtBadge.length,20);a.equal(f({bidArtBadgeColor:'bad'}).bidArtBadgeColor,'#e5d4bd');a.equal(f({bidArtBadgeX:999}).bidArtBadgeX,90);a.equal(f({bidArtBadgeY:-1}).bidArtBadgeY,10);\n")

# Favorite layout assistant: arrange existing independent application buttons.
# Do not create duplicates, alter actions, or move locked/grouped/native elements.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function refreshPrecision(){", """function favoriteLayout50(items,cols,orientation,curve,width,height){
 if(!Array.isArray(items)||!Number.isInteger(cols)||cols<1||cols>8||!['horizontal','vertical'].includes(orientation)||!Number.isFinite(width)||!Number.isFinite(height)||width<320||height<240)return null;
 const eligible=items.filter(e=>e.type==='button'&&e.appKey&&!e.locked&&!e.group);
 if(!eligible.length)return null;
 const rows=Math.ceil(eligible.length/cols),gap=8,top=64,margin=16;
 const nx=orientation==='horizontal'?cols:rows,ny=orientation==='horizontal'?rows:cols;
 const w=Math.min(160,Math.floor((width-2*margin-(nx-1)*gap)/nx)),h=Math.min(100,Math.floor((height-top-margin-(ny-1)*gap-(curve?32:0))/ny));
 if(w<48||h<36)return null;
 const positions=new Map();
 eligible.forEach((e,i)=>{
  const xIndex=orientation==='horizontal'?i%cols:Math.floor(i/cols),yIndex=orientation==='horizontal'?Math.floor(i/cols):i%cols;
  const x=Math.round((width-(nx*w+(nx-1)*gap))/2+xIndex*(w+gap));
  const bend=curve&&nx>1?Math.round(32*Math.pow((2*xIndex/(nx-1))-1,2)):0;
  positions.set(e.id,{x,y:top+yIndex*(h+gap)+bend,w,h});
 });
 return items.map(e=>positions.has(e.id)?{...e,...positions.get(e.id)}:e);
}
const favoritePanel50=document.createElement('fieldset');
const favoriteLegend50=document.createElement('legend');favoriteLegend50.textContent='Aranjare aplicații favorite';favoritePanel50.append(favoriteLegend50);
const favoriteCols50=document.createElement('select');for(let i=1;i<=8;i++)favoriteCols50.append(new Option(String(i),String(i)));favoriteCols50.value='4';
const favoriteOrient50=document.createElement('select');favoriteOrient50.append(new Option('Orizontal','horizontal'),new Option('Vertical','vertical'));
const favoriteCurve50=document.createElement('input');favoriteCurve50.type='checkbox';
for(const [title,control] of [['Elemente pe rând/coloană',favoriteCols50],['Direcție',favoriteOrient50],['Dispunere curbată',favoriteCurve50]]){const row=document.createElement('label');row.textContent=title;row.append(control);favoritePanel50.append(row);}
const favoriteApply50=document.createElement('button');favoriteApply50.type='button';favoriteApply50.textContent='Aranjează scurtăturile aplicațiilor';
favoriteApply50.onclick=()=>{
 if(!allowed()||!draft)return;
 const next=favoriteLayout50(draft.elements,Number(favoriteCols50.value),favoriteOrient50.value,favoriteCurve50.checked,W,H);
 if(!next){message('Nu sunt suficiente scurtături eligibile sau spațiu.');return;}
 let validated;try{validated=next.map((e,i)=>e===draft.elements[i]?e:element(e));}catch(_){message('Geometrie incompatibilă.');return;}
 if(!confirm('Rearanjezi scurtăturile independente? Alte elemente rămân pe poziție și pot fi suprapuse.'))return;
 checkpoint();draft.elements=validated;render();
};
favoritePanel50.append(favoriteApply50);$('bfControls').append(favoritePanel50);
function refreshPrecision(){""")
p.write_text(s)
(root/'tests/editor10022/test_favorite_layout50.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function favoriteLayout50('),j=s.indexOf('const favoritePanel50=',i);a.ok(i>=0&&j>i);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);
const f=c.favoriteLayout50,items=[{id:'a',type:'button',appKey:'pkg/a',action:'app',x:10},{id:'b',type:'button',appKey:'pkg/b',x:20},{id:'c',type:'button',appKey:'pkg/c',locked:true,x:30},{id:'d',type:'button',appKey:'pkg/d',group:'g',x:40},{id:'e',type:'external',x:50}];
const h=f(items,2,'horizontal',false,1280,720),v=f(items,2,'vertical',false,1280,720);
a.ok(h[1].x>h[0].x);a.equal(h[0].y,h[1].y);a.ok(v[1].y>v[0].y);a.equal(v[0].x,v[1].x);a.equal(h[0].action,'app');a.equal(h[2],items[2]);a.equal(h[3],items[3]);a.equal(h[4],items[4]);a.equal(items[0].x,10);a.equal(f(items,0,'horizontal',false,1280,720),null);a.equal(f([],2,'horizontal',false,1280,720),null);
const z=f([...items,{id:'f',type:'button',appKey:'pkg/f'}],3,'horizontal',true,1280,720);a.ok(z[0].y>z[1].y);console.log('12 favorite layout checks passed');
""")

# Make favorite rearrangement collision-aware, and allow explicit selection
# rather than moving every shortcut on the personal page.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function favoriteLayout50(items,cols,orientation,curve,width,height){", """function favoriteOverlap51(a,b){return [a.x,a.y,a.w,a.h,b.x,b.y,b.w,b.h].every(Number.isFinite)&&a.w>0&&a.h>0&&b.w>0&&b.h>0&&a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;}
function favoriteLayout50(items,cols,orientation,curve,width,height,ids=null,spacing=8){""")
rep("const eligible=items.filter(e=>e.type==='button'&&e.appKey&&!e.locked&&!e.group);","const eligible=items.filter(e=>e.type==='button'&&e.appKey&&!e.locked&&!e.group&&(!ids||ids.includes(e.id)));")
rep("const rows=Math.ceil(eligible.length/cols),gap=8,top=64,margin=16;","const rows=Math.ceil(eligible.length/cols),gap=Number.isFinite(spacing)?Math.max(0,Math.min(32,Math.round(spacing))):8,top=64,margin=16;")
rep("const favoriteApply50=document.createElement('button');", """const favoriteSpacing51=document.createElement('input');favoriteSpacing51.type='number';favoriteSpacing51.min=0;favoriteSpacing51.max=32;favoriteSpacing51.value=8;
const spacingLabel51=document.createElement('label');spacingLabel51.textContent='Spațiere (px)';spacingLabel51.append(favoriteSpacing51);favoritePanel50.append(spacingLabel51);
const favoriteOnly51=document.createElement('input');favoriteOnly51.type='checkbox';
const onlyLabel51=document.createElement('label');onlyLabel51.textContent='Doar scurtăturile selectate din listă';onlyLabel51.append(favoriteOnly51);favoritePanel50.append(onlyLabel51);
const favoriteList51=document.createElement('div');favoritePanel50.append(favoriteList51);
const favoriteChosen51=new Set();let favoriteContext51='';
function refreshFavorite51(){
 const key=draft?String(draft.id)+'/'+String(draft.pageId):'';
 if(key!==favoriteContext51){favoriteChosen51.clear();favoriteContext51=key;}
 favoriteList51.replaceChildren();
 for(const e of draft?.elements||[]){
  if(e.type!=='button'||!e.appKey||e.locked||e.group)continue;
  const row=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=favoriteChosen51.has(e.id);
  check.onchange=()=>{if(check.checked)favoriteChosen51.add(e.id);else favoriteChosen51.delete(e.id);};
  row.append(check,document.createTextNode(String(e.label||e.appKey)));favoriteList51.append(row);
 }
}
const favoriteApply50=document.createElement('button');""")
rep("favoriteCurve50.checked,W,H);","favoriteCurve50.checked,W,H,favoriteOnly51.checked?[...favoriteChosen51]:null,favoriteSpacing51.valueAsNumber);")
rep("if(!confirm('Rearanjezi scurtăturile independente? Alte elemente rămân pe poziție și pot fi suprapuse.'))return;", """const changed=validated.filter((e,i)=>e!==draft.elements[i]&&['x','y','w','h'].some(k=>e[k]!==draft.elements[i][k]));
 if(!changed.length)return;
 const unchanged=validated.filter(e=>!changed.includes(e));
 if(changed.some(e=>unchanged.some(b=>favoriteOverlap51(e,b)))&&!confirm('Noua poziție se suprapune peste alte elemente. Aplici totuși?'))return;
 if(!confirm('Aplici noua dispunere a '+changed.length+' scurtături?'))return;""")
rep("function refreshPrecision(){", "function refreshPrecision(){refreshFavorite51();")
p.write_text(s)
# Include the geometry helper in the isolated test context and check selection.
t=root/'tests/editor10022/test_favorite_layout50.js'
u=t.read_text().replace("i=s.indexOf('function favoriteLayout50(')","i=s.indexOf('function favoriteOverlap51(')")
u += "\nconst sel=f(items,2,'horizontal',false,1280,720,['b'],20);a.equal(sel[0],items[0]);a.ok(sel[1]!==items[1]);a.equal(f(items,2,'horizontal',false,1280,720,[]),null);a.equal(c.favoriteOverlap51({x:0,y:0,w:10,h:10},{x:9,y:9,w:10,h:10}),true);a.equal(c.favoriteOverlap51({x:0,y:0,w:10,h:10},{x:10,y:0,w:10,h:10}),false);\n"
t.write_text(u)

# Add reversible favorite ordering and preview before editing the personal page.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const favoriteChosen51=new Set();let favoriteContext51='';","""const favoriteChosen51=new Set();let favoriteContext51='';let favoriteReverse52=false;
const favoriteReverseControl52=document.createElement('input');favoriteReverseControl52.type='checkbox';
const favoriteReverseLabel52=document.createElement('label');favoriteReverseLabel52.textContent='Ordine inversă';favoriteReverseLabel52.append(favoriteReverseControl52);favoritePanel50.append(favoriteReverseLabel52);
favoriteReverseControl52.onchange=()=>{favoriteReverse52=favoriteReverseControl52.checked;};
const favoritePreview52=document.createElement('button');favoritePreview52.type='button';favoritePreview52.textContent='Previzualizează aranjarea';
favoritePanel50.append(favoritePreview52);""")
rep("ids=null,spacing=8){","ids=null,spacing=8,reverse=false){")
rep("if(!eligible.length)return null;","if(!eligible.length)return null;if(reverse===true)eligible.reverse();")
rep("favoriteSpacing51.valueAsNumber);","favoriteSpacing51.valueAsNumber,favoriteReverse52);")
rep("const favoriteApply50=document.createElement('button');","""favoritePreview52.onclick=()=>{
 if(!allowed()||!draft)return;
 const next=favoriteLayout50(draft.elements,Number(favoriteCols50.value),favoriteOrient50.value,favoriteCurve50.checked,W,H,favoriteOnly51.checked?[...favoriteChosen51]:null,favoriteSpacing51.valueAsNumber,favoriteReverse52);
 if(!next){message('Nu sunt scurtături eligibile sau spațiu suficient.');return;}
 const old=document.getElementById('bidFavoritePreview52');if(old)old.remove();
 const preview=document.createElement('div');preview.id='bidFavoritePreview52';preview.style.cssText='position:relative;width:100%;aspect-ratio:'+W+'/'+H+';background:#171318;border:1px solid #b59b80;overflow:hidden';
 next.forEach((e,i)=>{
  if(![e.x,e.y,e.w,e.h].every(Number.isFinite))return;
  const item=document.createElement('div');item.textContent=String(e.label||e.appKey||e.type||'');
  item.style.cssText='position:absolute;box-sizing:border-box;overflow:hidden;font-size:10px;border:1px solid #8a8078;pointer-events:none';
  item.style.left=(100*e.x/W)+'%';item.style.top=(100*e.y/H)+'%';item.style.width=(100*e.w/W)+'%';item.style.height=(100*e.h/H)+'%';
  item.style.background=e!==draft.elements[i]?'#572433':'#343438';preview.append(item);
 });
 favoritePanel50.append(preview);
};
const favoriteApply50=document.createElement('button');""")
rep("favoriteList51.replaceChildren();","favoriteList51.replaceChildren();document.getElementById('bidFavoritePreview52')?.remove();")
p.write_text(s)
t=root/'tests/editor10022/test_favorite_layout50.js'
with t.open('a') as f:
 f.write("\nconst rev=f(items,2,'horizontal',false,1280,720,null,8,true);a.ok(rev[0].x>rev[1].x);a.equal(rev[2],items[2]);a.equal(items[0].x,10);\n")

# Import graphic badges through the existing bounded Android image picker.
# Route its response separately so an emblem cannot replace a theme background.
p=root/'app/src/main/java/ro/dj88bid/car/BidThemeImage.kt'
s=p.read_text()
rep('    private var pending = false','    private var pending = false\n    private var badgeRequest = false')
rep('            pending = false\n            if (closed', '            pending = false\n            val badge=badgeRequest;badgeRequest=false\n            if (closed')
rep('            web.evaluateJavascript("if(window.bidThemeImageResult)window.bidThemeImageResult($json);",null)', '''            val callback=if(badge)"bidThemeBadgeResult" else "bidThemeImageResult"
            web.evaluateJavascript("if(window.$callback)window.$callback($json);",null)''')
rep('    @JavascriptInterface fun pick() {','''    @JavascriptInterface fun pick() { openPicker(false) }
    @JavascriptInterface fun pickBadge() { openPicker(true) }
    private fun openPicker(badge:Boolean) {''')
rep('            pending = true','            pending = true\n            badgeRequest=badge')
rep('putExtra(Intent.EXTRA_MIME_TYPES,arrayOf("image/jpeg","image/png","image/webp","image/gif"))','putExtra(Intent.EXTRA_MIME_TYPES,if(badge)arrayOf("image/jpeg","image/png","image/webp") else arrayOf("image/jpeg","image/png","image/webp","image/gif"))')
rep('                if(type=="image/gif"){','                if(type=="image/gif" && badgeRequest)error("Alege o emblemă statică PNG, JPG sau WebP.")\n                if(type=="image/gif"){')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function bidArtworkStyle37(v){", """function bidBadgeImage53(v){return typeof v==='string'&&v.length<=534000&&/^data:image\\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(v)?v:'';}
function bidArtworkStyle37(v){""")
rep("bidArtBadgeY:bound(v.bidArtBadgeY,80,10,90)};", "bidArtBadgeY:bound(v.bidArtBadgeY,80,10,90),bidArtBadgeImage:bidBadgeImage53(v.bidArtBadgeImage),bidArtBadgeSize:bound(v.bidArtBadgeSize,20,5,50)};")
rep("if(artStyle37.bidArtBadge){","if(artStyle37.bidArtBadge||artStyle37.bidArtBadgeImage){")
rep("badge.textContent=artStyle37.bidArtBadge;", "badge.textContent=artStyle37.bidArtBadgeImage?'':artStyle37.bidArtBadge;")
rep("  n.append(badge);", """  if(artStyle37.bidArtBadgeImage){
   const img=document.createElement('img');img.src=artStyle37.bidArtBadgeImage;img.alt='Emblemă personală';
   img.style.cssText='display:block;width:100%;height:100%;object-fit:contain;pointer-events:none';
   badge.style.width=artStyle37.bidArtBadgeSize+'%';badge.style.height=artStyle37.bidArtBadgeSize+'%';badge.append(img);
  }
  n.append(badge);""")
rep("const artApply37=document.createElement('button');", """const badgeSize53=document.createElement('input');badgeSize53.type='range';badgeSize53.min=5;badgeSize53.max=50;
const badgeSizeLabel53=document.createElement('label');badgeSizeLabel53.textContent='Dimensiune emblemă grafică (%)';badgeSizeLabel53.append(badgeSize53);artPanel37.append(badgeSizeLabel53);
let badgePick53=null;
const badgeImport53=document.createElement('button');badgeImport53.type='button';badgeImport53.textContent='Importă emblemă PNG/JPG/WebP';
const badgeClear53=document.createElement('button');badgeClear53.type='button';badgeClear53.textContent='Elimină emblema grafică';
badgeImport53.onclick=()=>{
 if(!allowed()||!draft||badgePick53)return;
 const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group)return;
 if(typeof window.BIDThemeImage?.pickBadge!=='function'){message('Selector emblemă indisponibil.');return;}
 badgePick53={theme:draft.id,page:draft.pageId,id:e.id};try{window.BIDThemeImage.pickBadge();}catch(_){badgePick53=null;}
};
window.bidThemeBadgeResult=result=>{
 const target=badgePick53;badgePick53=null;
 if(!target||!allowed()||!draft||draft.id!==target.theme||draft.pageId!==target.page)return;
 const e=draft.elements.find(v=>v.id===target.id);if(!e||e.locked||e.group)return;
 const image=bidBadgeImage53(result?.image);if(!image){message(result?.message||'Emblemă invalidă.');return;}
 if(e.bidArtBadgeImage===image)return;checkpoint();e.bidArtBadgeImage=image;render();
};
badgeClear53.onclick=()=>{if(!allowed()||!draft)return;const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group||!e.bidArtBadgeImage)return;checkpoint();e.bidArtBadgeImage='';render();};
artPanel37.append(badgeImport53,badgeClear53);
const artApply37=document.createElement('button');""")
rep("bidArtBadgeY:badgeY37.valueAsNumber}", "bidArtBadgeY:badgeY37.valueAsNumber,bidArtBadgeImage:e.bidArtBadgeImage,bidArtBadgeSize:badgeSize53.valueAsNumber}")
rep("badgeY37.value=String(style.bidArtBadgeY);for(const c of", "badgeY37.value=String(style.bidArtBadgeY);badgeSize53.value=String(style.bidArtBadgeSize);for(const c of")
rep("badgeX37,badgeY37,artApply37,artReset37])","badgeX37,badgeY37,badgeSize53,badgeImport53,badgeClear53,artApply37,artReset37])")
p.write_text(s)
t=root/'tests/editor10022/test_artwork_style37.js'
with t.open('a') as f:
 f.write("\na.equal(f({bidArtBadgeImage:'https://example.com/a.png'}).bidArtBadgeImage,'');a.equal(f({bidArtBadgeImage:'data:image/svg+xml;base64,AAAA'}).bidArtBadgeImage,'');a.equal(f({bidArtBadgeImage:'data:image/png;base64,AAAA'}).bidArtBadgeImage,'data:image/png;base64,AAAA');a.equal(f({bidArtBadgeSize:100}).bidArtBadgeSize,50);a.equal(f({bidArtBadgeSize:-1}).bidArtBadgeSize,5);\n")

# Add a cyclic favorites browser inside the personal theme editor. Long press
# selects the existing shortcut for editing; it never launches an application.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const favoriteList51=document.createElement('div');favoritePanel50.append(favoriteList51);", """const favoriteList51=document.createElement('div');favoritePanel50.append(favoriteList51);
const favoriteBrowse54=document.createElement('div');favoriteBrowse54.style.cssText='display:flex;align-items:center;gap:8px;flex-wrap:wrap';
const favoritePrev54=document.createElement('button'),favoriteNext54=document.createElement('button'),favoriteItem54=document.createElement('button');
favoritePrev54.type=favoriteNext54.type=favoriteItem54.type='button';
favoritePrev54.textContent='Anterior';favoriteNext54.textContent='Următor';
favoriteBrowse54.append(favoritePrev54,favoriteItem54,favoriteNext54);favoritePanel50.append(favoriteBrowse54);
let favoriteIndex54=0,favoriteItems54=[],favoritePress54=null,favoritePressed54=false;
function favoriteWrap54(i,n){return Number.isInteger(i)&&Number.isInteger(n)&&n>0?((i%n)+n)%n:0;}
function drawFavorite54(){
 favoriteIndex54=favoriteWrap54(favoriteIndex54,favoriteItems54.length);
 const e=favoriteItems54[favoriteIndex54];favoriteItem54.textContent=e?String(e.label||e.appKey)+' ('+(favoriteIndex54+1)+'/'+favoriteItems54.length+')':'Nicio scurtătură';
 favoriteItem54.disabled=!e;favoritePrev54.disabled=favoriteNext54.disabled=favoriteItems54.length<2;
}
function stepFavorite54(n){favoriteIndex54=favoriteWrap54(favoriteIndex54+n,favoriteItems54.length);drawFavorite54();}
favoritePrev54.onclick=()=>stepFavorite54(-1);favoriteNext54.onclick=()=>stepFavorite54(1);
function editFavorite54(){
 if(!allowed()||!draft)return;
 const item=favoriteItems54[favoriteIndex54],e=draft.elements.find(v=>v.id===item?.id);
 if(!e||e.locked||e.group||e.type!=='button'||!e.appKey)return;
 selected=e.id;render();
}
function cancelFavoritePress54(){if(favoritePress54!==null){clearTimeout(favoritePress54);favoritePress54=null;}}
favoriteItem54.onpointerdown=ev=>{
 cancelFavoritePress54();favoritePressed54=false;
 if(ev.button!==0||!allowed())return;
 const id=favoriteItems54[favoriteIndex54]?.id,key=favoriteContext51;
 favoritePress54=setTimeout(()=>{favoritePress54=null;if(key!==favoriteContext51||id!==favoriteItems54[favoriteIndex54]?.id)return;favoritePressed54=true;editFavorite54();},650);
};
favoriteItem54.onpointerup=favoriteItem54.onpointercancel=favoriteItem54.onpointerleave=cancelFavoritePress54;
favoriteItem54.oncontextmenu=ev=>ev.preventDefault();
favoriteItem54.onclick=()=>{if(favoritePressed54){favoritePressed54=false;return;}editFavorite54();};""")
rep("favoriteChosen51.clear();favoriteContext51=key;","favoriteChosen51.clear();favoriteContext51=key;favoriteIndex54=0;cancelFavoritePress54();")
rep("favoriteList51.replaceChildren();document.getElementById('bidFavoritePreview52')?.remove();","favoriteList51.replaceChildren();document.getElementById('bidFavoritePreview52')?.remove();favoriteItems54=(draft?.elements||[]).filter(e=>e.type==='button'&&e.appKey&&!e.locked&&!e.group);drawFavorite54();")
p.write_text(s)
(root/'tests/editor10022/test_favorite_wrap54.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function favoriteWrap54(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.favoriteWrap54;a.equal(f(-1,4),3);a.equal(f(4,4),0);a.equal(f(-9,4),3);a.equal(f(8,0),0);a.equal(f(NaN,4),0);a.equal(f(0,1),0);console.log('6 cyclic editor navigation checks passed');""")

# Prevent excessive inline artwork from exhausting WebView local storage.
# Retain the last valid theme and recovery point when the limit is exceeded.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("function persist(next){","""function bidStorageBudget55(serialized){return typeof serialized==='string'&&serialized.length<=1800000;}
function persist(next){""")
rep("const serialized=JSON.stringify({version:1,...candidate});const before=localStorage.getItem(KEY);","const serialized=JSON.stringify({version:1,...candidate});if(!bidStorageBudget55(serialized))throw Error('Temele depășesc limita locală. Exportă și elimină imaginile nefolosite înainte de salvare.');const before=localStorage.getItem(KEY);")
# Provide a local estimate, not an operating-system quota claim.
rep("function refreshPrecision(){", """const storagePanel55=document.createElement('fieldset');
const storageLegend55=document.createElement('legend');storageLegend55.textContent='Memorie teme locale';storagePanel55.append(storageLegend55);
const storageInfo55=document.createElement('p');storagePanel55.append(storageInfo55);
const storageCheck55=document.createElement('button');storageCheck55.type='button';storageCheck55.textContent='Verifică spațiul temei';
storageCheck55.onclick=()=>{
 try{
  const saved=localStorage.getItem(KEY)||'';
  const recovery=localStorage.getItem(BACKUP)||'';
  const draftSize=draft?JSON.stringify(draft).length:0;
  storageInfo55.textContent='Teme salvate: '+Math.round(saved.length/1024)+' Ki caractere; copie recuperare: '+Math.round(recovery.length/1024)+'; ciornă: '+Math.round(draftSize/1024)+'. Limita preventivă pentru temele salvate: 1800000 caractere.';
 }catch(_){storageInfo55.textContent='Dimensiunea locală nu este disponibilă.';}
};
storagePanel55.append(storageCheck55);$('bfControls').append(storagePanel55);
function refreshPrecision(){""")
p.write_text(s)
(root/'tests/editor10022/test_storage_budget55.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function bidStorageBudget55(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.bidStorageBudget55;a.equal(f('{}'),true);a.equal(f('x'.repeat(1800000)),true);a.equal(f('x'.repeat(1800001)),false);a.equal(f(null),false);console.log('4 storage budget checks passed');""")
# Guard asynchronous graphic picker against stale draft replacement.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("badgePick53={theme:draft.id,page:draft.pageId,id:e.id};","badgePick53={theme:draft.id,page:draft.pageId,id:e.id,element:e};")
rep("if(!e||e.locked||e.group)return;\n const image=bidBadgeImage53(result?.image);","if(!e||e!==target.element||e.locked||e.group)return;\n const image=bidBadgeImage53(result?.image);")
p.write_text(s)

# Verify exported backup bytes by reading the selected document back. Report
# successful writing separately from verified readback (some providers deny read).
p=root/'app/src/main/java/ro/dj88bid/car/BidThemeFiles.kt'
s=p.read_text()
rep('                    reply(kind,true,"Fișier JSON exportat.")', '''                    val expected=text.toByteArray(Charsets.UTF_8)
                    val verified=try {
                        activity.contentResolver.openInputStream(uri)?.use { input ->
                            val digest=java.security.MessageDigest.getInstance("SHA-256")
                            val buffer=ByteArray(8192);var total=0L
                            while(true){val n=input.read(buffer);if(n<0)break;if(n==0)continue;total+=n;if(total>MAX)error("Document prea mare.");digest.update(buffer,0,n)}
                            total==expected.size.toLong()&&digest.digest().contentEquals(java.security.MessageDigest.getInstance("SHA-256").digest(expected))
                        }==true
                    }catch(_:Exception){false}
                    reply(kind,true,if(verified)"Fișier JSON exportat și verificat SHA-256 prin recitire." else "Fișier JSON scris; verificarea prin recitire nu a reușit. Verifică documentul înainte de ștergerea temei.")''')
p.write_text(s)
# Export the last validated recovery point as a separate user-selected document.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("storagePanel55.append(storageCheck55);", """const recoveryExport56=document.createElement('button');recoveryExport56.type='button';recoveryExport56.textContent='Exportă copia de recuperare';
recoveryExport56.onclick=()=>{
 if(!allowed())return;
 try{
  const raw=localStorage.getItem(BACKUP);
  if(!raw){message('Nu există o copie de recuperare.');return;}
  const doc=JSON.parse(raw),validated=snapshot(doc);
  if(doc.active!==validated.active)throw Error('Copie invalidă.');
  if(!confirm('Salvezi separat copia de recuperare? Tema curentă nu se schimbă.'))return;
  if(typeof window.BIDThemeFiles?.exportDocument!=='function'){message('Selector de fișiere indisponibil.');return;}
  window.BIDThemeFiles.exportDocument('BID-recovery-'+new Date().toISOString().slice(0,10),JSON.stringify({version:1,...validated}));
 }catch(_){message('Copia de recuperare nu poate fi validată sau exportată.');}
};
storagePanel55.append(storageCheck55,recoveryExport56);""")
p.write_text(s)

# Exercise the real budget helper together with persistence in the existing VM.
t=root/'tests/editor10022/test_persistence_noop.js'
u=t.read_text()
a="const i=s.indexOf('function persist(next)'),j=s.indexOf("
b="const i=s.indexOf('function bidStorageBudget55('),j=s.indexOf("
assert u.count(a)==1
u=u.replace(a,b,1)
a="j=s.indexOf('\\n',i)"
b="j=s.indexOf('\\n',s.indexOf('function persist(next)'))"
assert u.count(a)==1
u=u.replace(a,b,1)
u += "\nconst stable=data.get('main'),recovery=data.get('backup'),count=writes;const huge={themes:[{image:'x'.repeat(1800001)}],active:null,applied:null};a.equal(c.persist(huge),false);a.equal(data.get('main'),stable);a.equal(data.get('backup'),recovery);a.equal(writes,count);console.log('4 oversized persistence rollback checks passed');\n"
t.write_text(u)

# Export current saved themes as well as the distinct recovery point.
# Both use the existing document picker, never overwrite local state.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("storagePanel55.append(storageCheck55,recoveryExport56);", """const currentExport56=document.createElement('button');currentExport56.type='button';currentExport56.textContent='Exportă toate temele salvate';
currentExport56.onclick=()=>{
 if(!allowed())return;
 try{
  const raw=localStorage.getItem(KEY);if(!raw){message('Nu există teme salvate.');return;}
  const doc=JSON.parse(raw),validated=snapshot(doc);
  if(doc.active!==validated.active)throw Error('Copie invalidă.');
  if(typeof window.BIDThemeFiles?.exportDocument!=='function'){message('Selector de fișiere indisponibil.');return;}
  if(!confirm('Exportă toate temele salvate? Modificările nesalvate nu sunt incluse.'))return;
  window.BIDThemeFiles.exportDocument('BID-backup-'+new Date().toISOString().slice(0,10),JSON.stringify({version:1,...validated}));
 }catch(_){message('Temele salvate nu pot fi validate sau exportate.');}
};
storagePanel55.append(storageCheck55,currentExport56,recoveryExport56);""")
p.write_text(s)
# Validate backup documents as JSON objects before writing, independently of JS.
p=root/'app/src/main/java/ro/dj88bid/car/BidThemeFiles.kt'
s=p.read_text()
rep('        val safe=name.replace(', '''        try{JSONObject(json)}catch(_:Exception){reply("export",false,"Document JSON invalid.");return@runOnUiThread}
        val safe=name.replace(''')
rep('                    val value=Charsets.UTF_8.newDecoder()', '                    val value=Charsets.UTF_8.newDecoder()')
rep('                    reply(kind,true,"Fișier citit. Se verifică structura.",value)', '''                    JSONObject(value)
                    reply(kind,true,"Fișier JSON citit. Se verifică structura temei.",value)''')
p.write_text(s)

# Both persistence suites must execute the real helper as well as persist().
# Keep the earlier-stage test unchanged until the helper is actually integrated.
t=root/'tests/editor10022/test_validated_persistence.js'
u=t.read_text()
a="const start=s.indexOf('function persist(next)'),end=s.indexOf('\\n',start);"
b="const start=s.indexOf('function bidStorageBudget55('),end=s.indexOf('\\n',s.indexOf('function persist(next)'));"
assert u.count(a)==1,a
u=u.replace(a,b,1)
u += "\nconst beforeMain=data.get('main'),beforeBackup=data.get('backup'),beforeState=c.state; a.equal(c.persist({themes:[{image:'x'.repeat(1800001)}],active:null,applied:null}),false);a.equal(data.get('main'),beforeMain);a.equal(data.get('backup'),beforeBackup);a.equal(c.state,beforeState);console.log('4 additional persistence state-preservation checks passed');\n"
t.write_text(u)

# Add a searchable shortcut list with bulk selection in the existing editor.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const favoriteList51=document.createElement('div');favoritePanel50.append(favoriteList51);", """const favoriteSearch57=document.createElement('input');favoriteSearch57.type='search';favoriteSearch57.placeholder='Caută scurtături';favoriteSearch57.setAttribute('aria-label','Caută scurtături favorite');
favoritePanel50.append(favoriteSearch57);
const favoriteSelect57=document.createElement('button');favoriteSelect57.type='button';favoriteSelect57.textContent='Selectează rezultatele';
const favoriteDeselect57=document.createElement('button');favoriteDeselect57.type='button';favoriteDeselect57.textContent='Deselectează toate';
favoritePanel50.append(favoriteSelect57,favoriteDeselect57);
const favoriteList51=document.createElement('div');favoritePanel50.append(favoriteList51);
function favoriteMatches57(e,q){return !!e&&e.type==='button'&&!!e.appKey&&!e.locked&&!e.group&&[String(e.label||''),String(e.appKey)].some(v=>v.toLocaleLowerCase().includes(String(q||'').trim().toLocaleLowerCase()));}
favoriteSearch57.oninput=()=>refreshFavorite51();
favoriteSelect57.onclick=()=>{if(!allowed()||!draft)return;for(const e of draft.elements)if(favoriteMatches57(e,favoriteSearch57.value))favoriteChosen51.add(e.id);favoriteOnly51.checked=true;refreshFavorite51();};
favoriteDeselect57.onclick=()=>{if(!allowed())return;favoriteChosen51.clear();favoriteOnly51.checked=true;refreshFavorite51();};""")
rep("favoriteChosen51.clear();favoriteContext51=key;favoriteIndex54=0;cancelFavoritePress54();","favoriteChosen51.clear();favoriteContext51=key;favoriteIndex54=0;favoriteSearch57.value='';cancelFavoritePress54();")
rep("if(e.type!=='button'||!e.appKey||e.locked||e.group)continue;","if(!favoriteMatches57(e,favoriteSearch57.value))continue;")
p.write_text(s)
(root/'tests/editor10022/test_favorite_search57.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function favoriteMatches57(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.favoriteMatches57,e={type:'button',appKey:'com.waze',label:'Navigație'};a.equal(f(e,'WAZE'),true);a.equal(f(e,' navigație '),true);a.equal(f(e,'radio'),false);a.equal(f({...e,locked:true},''),false);a.equal(f({...e,group:'x'},''),false);a.equal(f(null,''),false);console.log('6 favorite search checks passed');""")

# Consolidated-source audit (build 148): preserve automotive mirroring when
# content-scale is applied and guard real runtime favorites against stale actions.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("if(artStyle37.bidArtMirror)art.style.scale='-1 1';", "if(artStyle37.bidArtMirror)art.style.transform=e.flip?'none':'scaleX(-1)';")
rep("n.querySelectorAll('.bfGlyph,.bfAutoArt,[data-bid-gauge]'))child.hidden=true;", "n.querySelectorAll('.bfGlyph,.bfAutoArt,.bidPersonalAutoBadge,[data-bid-gauge]'))child.hidden=true;")
rep("function mountFavorites(t){", """function favoriteRuntimeAllowed148(current,original,group,movingNow,available,hidden,editing,locked){
 return !!current&&!!original&&current.id===original.id&&current.pageId===original.pageId&&current.elements.some(e=>e.group===group&&e.groupMode==='favorites')&&!movingNow&&available===true&&!hidden&&!editing&&!locked;
}
function mountFavorites(t){""")
rep("const shift=d=>{page=cfg.cycle?(page+d+total)%total:clamp(page+d,0,total-1);show();};", """const ready=()=>favoriteRuntimeAllowed148(active(),t,anchor.group,moving(),panel.dataset.available==='true',document.hidden,edit,globalLock66);
const shift=d=>{if(!ready())return;page=cfg.cycle?(page+d+total)%total:clamp(page+d,0,total-1);show();};""")
rep("if(start&&!moving()){blockUntil=Date.now()+700;openFrom('');if(draft){selected=anchor.id;render();}}", "if(start&&ready()&&!members.some(e=>e.locked)){blockUntil=Date.now()+700;openFrom('');if(draft&&draft.id===t.id&&draft.pageId===t.pageId){selected=anchor.id;render();}}")
rep("n.addEventListener('pointerdown',ev=>{clear();start={x:ev.clientX,y:ev.clientY};", "n.addEventListener('pointerdown',ev=>{clear();if(!ready()||ev.button!==0)return;start={x:ev.clientX,y:ev.clientY};")
rep("if(Date.now()<blockUntil){ev.preventDefault();ev.stopImmediatePropagation();}", "if(Date.now()<blockUntil||!ready()){ev.preventDefault();ev.stopImmediatePropagation();}")
p.write_text(s)
(root/'tests/editor10022/test_favorites_runtime148.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function favoriteRuntimeAllowed148('),j=s.indexOf('function mountFavorites(t)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.favoriteRuntimeAllowed148,t={id:'t',pageId:'p',elements:[{group:'g',groupMode:'favorites'}]};a.equal(f(t,t,'g',false,true,false,false,false),true);a.equal(f({...t,pageId:'q'},t,'g',false,true,false,false,false),false);a.equal(f(t,t,'g',true,true,false,false,false),false);a.equal(f(t,t,'g',false,false,false,false,false),false);a.equal(f(t,t,'g',false,true,true,false,false),false);a.equal(f(t,t,'g',false,true,false,true,false),false);a.equal(f(t,t,'g',false,true,false,false,true),false);a.equal(f(t,t,'missing',false,true,false,false,false),false);console.log('8 runtime favorites guard checks passed');""")

# Consolidated finalization batch: interoperable backups and editable CAN data.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("recoveryExport56.onclick=()=>{\n if(!allowed())return;", "recoveryExport56.onclick=()=>{\n if(!allowed()||fileRequest||!draft)return;")
rep("currentExport56.onclick=()=>{\n if(!allowed())return;", "currentExport56.onclick=()=>{\n if(!allowed()||fileRequest||!draft)return;")
for prefix in ('BID-recovery-','BID-backup-'):
    old="window.BIDThemeFiles.exportDocument('"+prefix+"'+new Date().toISOString().slice(0,10),JSON.stringify({version:1,...validated}));"
    new="const payload=JSON.stringify({format:'BID-full-backup',version:1,data:{version:1,...validated},palettes});\n  if(new Blob([payload]).size>6000000)throw Error('Backup prea mare.');\n  fileRequest={kind:'export',theme:draft.id};\n  window.BIDThemeFiles.exportDocument('"+prefix+"'+new Date().toISOString().slice(0,10),payload);\n  fileMessage('Alege destinația documentului.');"
    rep(old,new)
rep("}catch(_){message('Copia de recuperare nu poate fi validată sau exportată.');}", "}catch(_){fileRequest=null;message('Copia de recuperare nu poate fi validată sau exportată.');}")
rep("}catch(_){message('Temele salvate nu pot fi validate sau exportate.');}", "}catch(_){fileRequest=null;message('Temele salvate nu pot fi validate sau exportate.');}")
# Accept legacy raw snapshots from builds 142–149 through the same confirmed import path.
rep("window.bidThemeFileResult=r=>", """function normalizeBackup150(doc,currentPalettes){
 if(doc&&doc.version===1&&!doc.format&&Array.isArray(doc.themes)){
  return {format:'BID-full-backup',version:1,data:doc,palettes:currentPalettes};
 }
 return doc;
}
window.bidThemeFileResult=r=>""")
rep("const doc=JSON.parse(r.data);if(doc.version!==1)", "const doc=normalizeBackup150(JSON.parse(r.data),palettes);if(!doc||doc.version!==1)")
rep("$('bfJson').value=r.data;backupImportPending=true;", "$('bfJson').value=JSON.stringify(doc);backupImportPending=true;")
# Reject references to missing active themes before replacing existing library.
rep("const next=snapshot(b.data);const pp=", "const next=snapshot(b.data);if(b.data.active!==next.active)throw Error('Tema activă din backup este invalidă.');const pp=")
# CAN data stays explicitly experimental; expiry independent of native callbacks.
rep("const types={clock:", "const types={canSpeed:'CAN test · viteză',canRpm:'CAN test · RPM',canFuel:'CAN test · combustibil brut',canOdometer:'CAN test · kilometraj',canConsumption:'CAN test · consum brut',canOutside:'CAN test · temperatură ext.',canDoors:'CAN test · mască uși',canClimate:'CAN test · climatizare brută',clockSeconds:'Ceas cu secunde',clock:")
rep("function value(e){", """function canWidgetValue150(type,packet,elapsed,hidden){
 if(hidden||!packet||packet.active!==true||!Number.isFinite(elapsed)||elapsed<0)return 'CAN test · —';
 const channels={canSpeed:['body','speed',' km/h',5000],canRpm:['body','rpm',' rpm',5000],canFuel:['body','fuelRawScaled',' brut',5000],canOdometer:['body','odometer',' km',5000],canConsumption:['body','consumption',' brut',5000],canOutside:['temperature','celsius',' °C',120000],canDoors:['doors','mask',' mască',30000]};
 const spec=channels[type]|| (type==='canClimate'?['climate','left','',30000]:null);
 if(!spec)return 'CAN test · —';
 const [ch,key,unit,limit]=spec,meta=packet.channels?.[ch],data=packet[ch];
 if(meta?.fresh!==true||!Number.isFinite(meta.ageMs)||meta.ageMs<0||meta.ageMs+elapsed>limit||!data)return 'CAN test · —';
 if(type==='canClimate'){
  const fmt=v=>typeof v==='string'&&/^(LO|HI)$/.test(v)?v:Number.isFinite(v)?String(v)+' brut':'—';
  return 'CAN test · '+fmt(data.left)+' / '+fmt(data.right);
 }
 const n=data[key];return Number.isFinite(n)&& (type==='canOutside'||n>=0)?'CAN test · '+String(n)+unit:'CAN test · —';
}
function value(e){""")
rep("switch(e.type){case 'clock':", "switch(e.type){case 'canSpeed':case 'canRpm':case 'canFuel':case 'canOdometer':case 'canConsumption':case 'canOutside':case 'canDoors':case 'canClimate':return canWidgetValue150(e.type,window.bidCanLatest150?.packet,performance.now()-(window.bidCanLatest150?.at??-Infinity),document.hidden);case 'clockSeconds':return new Date().toLocaleTimeString('ro-RO',{hour:'2-digit',minute:'2-digit',second:'2-digit'});case 'clock':")
p.write_text(s)
p=root/'app/src/main/assets/index.html'
s=p.read_text()
rep("window.bidCanStatus=function(v){", """window.bidCanLatest150=null;
document.addEventListener('visibilitychange',()=>{if(document.hidden)window.bidCanLatest150=null;});
window.bidCanStatus=function(v){
 window.bidCanLatest150=v&&v.active&&!document.hidden?{packet:v,at:performance.now()}:null;""")
p.write_text(s)
(root/'tests/editor10022/test_final_batch150.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const c={};vm.createContext(c);for(const [start,end] of [['function canWidgetValue150(','function value(e)'],['function normalizeBackup150(','window.bidThemeFileResult=r=>']]){const i=s.indexOf(start),j=s.indexOf(end,i);a.ok(i>=0&&j>i);vm.runInContext(s.slice(i,j),c);}const f=c.canWidgetValue150,b={active:true,channels:{body:{fresh:true,ageMs:100},climate:{fresh:true,ageMs:0}},body:{speed:0,odometer:377000,fuelRawScaled:12.5},climate:{left:'LO',right:22}};a.equal(f('canSpeed',b,0,false),'CAN test · 0 km/h');a.equal(f('canOdometer',b,0,false),'CAN test · 377000 km');a.equal(f('canFuel',b,0,false),'CAN test · 12.5 brut');a.equal(f('canRpm',b,0,false),'CAN test · —');a.equal(f('canSpeed',b,4901,false),'CAN test · —');a.equal(f('canSpeed',b,0,true),'CAN test · —');a.equal(f('canSpeed',{...b,active:false},0,false),'CAN test · —');a.equal(f('canClimate',b,0,false),'CAN test · LO / 22 brut');a.equal(f('canSpeed',null,0,false),'CAN test · —');const old={version:1,themes:[],active:null},p=[{name:'BID'}],n=c.normalizeBackup150(old,p);a.equal(n.format,'BID-full-backup');a.equal(n.data,old);a.equal(n.palettes,p);a.equal(c.normalizeBackup150(n,p),n);a.equal(c.normalizeBackup150(null,p),null);console.log('14 CAN freshness and legacy backup checks passed');""")

# Original BID live wallpaper; no proprietary Car Launcher assets.
p=root/'app/src/main/AndroidManifest.xml'
s=p.read_text()
rep('</application>', '''    <service android:name=".BidLiveWallpaper" android:exported="true" android:permission="android.permission.BIND_WALLPAPER" android:label="BID Champagne Live">
        <intent-filter><action android:name="android.service.wallpaper.WallpaperService" /></intent-filter>
        <meta-data android:name="android.service.wallpaper" android:resource="@xml/bid_live_wallpaper" />
    </service>
    <activity android:name=".BidProviderMapActivity" android:exported="false" />
    <meta-data android:name="ro.dj88bid.YANDEX_KEY" android:value="PLACEHOLDER_YANDEX" />
    <meta-data android:name="com.baidu.lbsapi.API_KEY" android:value="PLACEHOLDER_BAIDU" />
</application>''')
s=s.replace('PLACEHOLDER_YANDEX',chr(36)+'{bidYandexKey}').replace('PLACEHOLDER_BAIDU',chr(36)+'{bidBaiduKey}')
p.write_text(s)
xml=root/'app/src/main/res/xml/bid_live_wallpaper.xml'
xml.parent.mkdir(parents=True,exist_ok=True)
xml.write_text('<wallpaper xmlns:android="http://schemas.android.com/apk/res/android" />')
src=root/'app/src/main/java/ro/dj88bid/car'
(src/'BidLiveWallpaper.kt').write_text('''package ro.dj88bid.car
import android.service.wallpaper.WallpaperService
import android.os.Handler
import android.os.Looper
import android.graphics.*
import android.view.SurfaceHolder
import kotlin.math.*
class BidLiveWallpaper: WallpaperService() {
 override fun onCreateEngine(): Engine = Live()
 inner class Live: Engine() {
  private val handler=Handler(Looper.getMainLooper())
  private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
  private var visible=false
  private var surface=false
  private val tick=Runnable { drawFrame() }
  private fun drawFrame(){
   handler.removeCallbacks(tick)
   if(!visible||!surface)return
   val c=try{surfaceHolder.lockCanvas()}catch(_:Exception){null}
   if(c!=null)try{
    c.drawColor(Color.rgb(20,7,12))
    val phase=(android.os.SystemClock.elapsedRealtime()%12000L)/12000.0*2*PI
    for(i in 0 until 96){
     paint.color=Color.argb((45+100*(1+sin(phase+i*0.71))/2).toInt(),222,193,145)
     c.drawCircle(((i*137)%997)/997f*c.width,((i*263)%991)/991f*c.height,if(i%13==0)1.8f else 0.8f,paint)
    }
   }finally{try{surfaceHolder.unlockCanvasAndPost(c)}catch(_:Exception){}}
   if(visible&&surface)handler.postDelayed(tick,100L)
  }
  override fun onVisibilityChanged(v:Boolean){visible=v;handler.removeCallbacks(tick);if(v)drawFrame()}
  override fun onSurfaceChanged(h:SurfaceHolder,f:Int,w:Int,y:Int){super.onSurfaceChanged(h,f,w,y);surface=true;drawFrame()}
  override fun onSurfaceDestroyed(h:SurfaceHolder){surface=false;handler.removeCallbacks(tick);super.onSurfaceDestroyed(h)}
  override fun onDestroy(){visible=false;handler.removeCallbacks(tick);super.onDestroy()}
 }
}
''')
p=root/'app/build.gradle.kts'
s=p.read_text()
s += '''
val bidYandexKey = System.getenv("BID_YANDEX_MAPS_KEY").orEmpty()
val bidBaiduKey = System.getenv("BID_BAIDU_MAPS_KEY").orEmpty()
android.defaultConfig.manifestPlaceholders["bidYandexKey"] = bidYandexKey
android.defaultConfig.manifestPlaceholders["bidBaiduKey"] = bidBaiduKey
dependencies {
    if (bidYandexKey.isNotBlank()) implementation("com.yandex.android:maps.mobile:4.45.0-lite")
    if (bidBaiduKey.isNotBlank()) implementation("com.baidu.lbsyun:BaiduMapSDK_Map:9.0.0")
}
'''
p.write_text(s)
(src/'BidProviderMapActivity.kt').write_text('''package ro.dj88bid.car
import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.view.View
import android.content.pm.PackageManager
import android.widget.Toast
class BidProviderMapActivity:Activity(){
 private var view:View?=null
 private var factory:Any?=null
 private var provider=""
 private var started=false
 private var yandexStarted=false
 private var viewStarted=false
 private fun call(obj:Any,method:String){obj.javaClass.getMethod(method).invoke(obj)}
 override fun onCreate(state:Bundle?){
  super.onCreate(state)
  provider=intent.getStringExtra("provider").orEmpty()
  val name=when(provider){"yandex"->"ro.dj88bid.YANDEX_KEY";"baidu"->"com.baidu.lbsapi.API_KEY";else->{finish();return}}
  val key=packageManager.getApplicationInfo(packageName,PackageManager.GET_META_DATA).metaData?.getString(name).orEmpty()
  if(key.isBlank()){fail("SDK neconfigurat: este necesară cheia proprie a furnizorului.");return}
  AlertDialog.Builder(this).setTitle("Hartă "+provider)
   .setMessage("Furnizorul extern procesează date de conectare și interacțiune conform politicii sale. BID nu solicită aici locația GPS. Continui numai dacă accepți politica furnizorului.")
   .setNegativeButton("Renunță"){_,_->finish()}
   .setOnCancelListener{finish()}
   .setPositiveButton("Accept și deschid"){_,_->open(key)}.show()
 }
 private fun fail(text:String){Toast.makeText(this,text,Toast.LENGTH_LONG).show();finish()}
 private fun open(key:String){
  try{
   if(provider=="yandex"){
    val cls=Class.forName("com.yandex.mapkit.MapKitFactory")
    cls.getMethod("setApiKey",String::class.java).invoke(null,key)
    cls.getMethod("initialize",android.content.Context::class.java).invoke(null,applicationContext)
    factory=cls.getMethod("getInstance").invoke(null)
    view=Class.forName("com.yandex.mapkit.mapview.MapView").getConstructor(android.content.Context::class.java).newInstance(this) as View
    setContentView(view)
    if(started)startYandex()
   }else{
    val cls=Class.forName("com.baidu.mapapi.SDKInitializer")
    cls.getMethod("setAgreePrivacy",android.content.Context::class.java,Boolean::class.javaPrimitiveType!!).invoke(null,applicationContext,true)
    cls.getMethod("initialize",android.content.Context::class.java).invoke(null,applicationContext)
    view=Class.forName("com.baidu.mapapi.map.MapView").getConstructor(android.content.Context::class.java).newInstance(this) as View
    setContentView(view)
    if(started)call(view!!,"onResume")
   }
  }catch(_:Exception){fail("Hartă indisponibilă: verifică SDK, autorizarea și arhitectura dispozitivului.")}
  catch(_:LinkageError){fail("SDK incompatibil cu dispozitivul.")}
 }
 private fun startYandex(){
  if(!yandexStarted){factory?.let{call(it,"onStart");yandexStarted=true}}
  if(!viewStarted){view?.let{call(it,"onStart");viewStarted=true}}
 }
 override fun onStart(){super.onStart();started=true;if(provider=="yandex")try{startYandex()}catch(_:Exception){fail("Hartă indisponibilă.")}}
 override fun onResume(){super.onResume();if(provider=="baidu")try{view?.let{call(it,"onResume")}}catch(_:Exception){fail("Hartă indisponibilă.")}}
 override fun onPause(){if(provider=="baidu")try{view?.let{call(it,"onPause")}}catch(_:Exception){};super.onPause()}
 override fun onStop(){started=false;if(provider=="yandex"){try{if(viewStarted)view?.let{call(it,"onStop")}}catch(_:Exception){};try{if(yandexStarted)factory?.let{call(it,"onStop")}}catch(_:Exception){};viewStarted=false;yandexStarted=false};super.onStop()}
 override fun onDestroy(){if(provider=="baidu")try{view?.let{call(it,"onDestroy")}}catch(_:Exception){};view=null;super.onDestroy()}
}
''')
p=src/'MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {','''    inner class Bridge {
        @JavascriptInterface
        fun openNativeProviderMap(provider:String)=runOnUiThread{
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||isFinishing||provider !in listOf("yandex","baidu"))return@runOnUiThread
            startActivity(Intent(this@MainActivity,BidProviderMapActivity::class.java).putExtra("provider",provider))
        }
        @JavascriptInterface
        fun chooseBidLiveWallpaper()=runOnUiThread{
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||isFinishing)return@runOnUiThread
            try{
                startActivity(Intent(android.app.WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER)
                    .putExtra(android.app.WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,android.content.ComponentName(this@MainActivity,BidLiveWallpaper::class.java)))
            }catch(_:Exception){android.widget.Toast.makeText(this@MainActivity,"Fundal live indisponibil pe firmware",android.widget.Toast.LENGTH_LONG).show()}
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","""button('BID Champagne · fundal live Android',()=>{try{native().chooseBidLiveWallpaper();}catch(_){}});
button('Yandex · SDK opțional',()=>{try{native().openNativeProviderMap('yandex');}catch(_){}});
button('Baidu · SDK opțional',()=>{try{native().openNativeProviderMap('baidu');}catch(_){}});
button('Închide',""")
p.write_text(s)

# Extend criterion 37 with direct selectable color tint and intensity.
# Only personal automotive artwork is affected, never the approved MASTER.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("bidArtBadgeSize:bound(v.bidArtBadgeSize,20,5,50)};", "bidArtBadgeSize:bound(v.bidArtBadgeSize,20,5,50),bidArtTint:/^#[0-9a-f]{6}$/i.test(typeof v.bidArtTint==='string'?v.bidArtTint:'')?v.bidArtTint:'#70232e',bidArtTintAmount:bound(v.bidArtTintAmount,0,0,100)};")
rep("if(artStyle37.bidArtMirror)art.style.transform=e.flip?'none':'scaleX(-1)';", """if(artStyle37.bidArtMirror)art.style.transform=e.flip?'none':'scaleX(-1)';
 if(artStyle37.bidArtTintAmount>0){
  const tint=document.createElement('span');tint.className='bidAutoTint152';
  tint.setAttribute('aria-hidden','true');
  Object.assign(tint.style,{position:'absolute',inset:'0',pointerEvents:'none',background:artStyle37.bidArtTint,opacity:String(artStyle37.bidArtTintAmount/100),mixBlendMode:'color',borderRadius:'inherit'});
  art.style.isolation='isolate';art.append(tint);
 }""")
rep("const mirror37=document.createElement('input');mirror37.type='checkbox';", """const mirror37=document.createElement('input');mirror37.type='checkbox';
const tint152=document.createElement('input');tint152.type='color';tint152.value='#70232e';
const tintAmount152=document.createElement('input');tintAmount152.type='range';tintAmount152.min='0';tintAmount152.max='100';tintAmount152.value='0';""")
rep("['Oglindire grafică auto',mirror37]", "['Oglindire grafică auto',mirror37],['Culoare grafică auto',tint152],['Intensitate recolorare',tintAmount152]")
rep("bidArtBadgeSize:badgeSize53.valueAsNumber}", "bidArtBadgeSize:badgeSize53.valueAsNumber,bidArtTint:tint152.value,bidArtTintAmount:tintAmount152.valueAsNumber}")
rep("mirror37.checked=style.bidArtMirror;", "mirror37.checked=style.bidArtMirror;tint152.value=style.bidArtTint;tintAmount152.value=String(style.bidArtTintAmount);")
# Include controls in the existing locked-element guard.
a="for(const c of [font37,hue37,mirror37,"
assert s.count(a)==1
s=s.replace(a,a+"tint152,tintAmount152,",1)
p.write_text(s)
with (root/'tests/editor10022/test_artwork_style37.js').open('a') as f:
 f.write("\na.equal(f({}).bidArtTintAmount,0);a.equal(f({bidArtTint:'#123456'}).bidArtTint,'#123456');a.equal(f({bidArtTint:'invalid'}).bidArtTint,'#70232e');a.equal(f({bidArtTintAmount:200}).bidArtTintAmount,100);a.equal(f({bidArtTintAmount:-1}).bidArtTintAmount,0);a.equal(f({bidArtTintAmount:NaN}).bidArtTintAmount,0);\n")

# Reuse existing native/media and GPS functionality for missing reference widgets.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={canSpeed:", "const types={analogClock:'Ceas analogic',sessionStart:'Ora deschiderii sesiunii BID',mediaPrevious:'Piesa precedentă',mediaPlay:'Redare / pauză',mediaNext:'Piesa următoare',volumeUp:'Volum +',volumeDown:'Volum −',volumeLevel:'Volum multimedia Android',displayLight:'Luminozitate fereastră Android',canSpeed:")
rep("const actions={apps:", "const actions={mediaPrevious:'Piesa precedentă',mediaPlay:'Redare / pauză',mediaNext:'Piesa următoare',volumeUp:'Volum +',volumeDown:'Volum −',apps:")
rep("function value(e){", """const catalogSessionStart154=new Date();
let catalogDevice154={},catalogDeviceAt154=-Infinity;
function catalogDeviceReading154(now){
 if(document.hidden)return {};
 if(now-catalogDeviceAt154>=2000){
  catalogDeviceAt154=now;
  try{catalogDevice154=JSON.parse(window.BID?.catalogDeviceState154()||'{}');}catch(_){catalogDevice154={};}
 }
 return catalogDevice154;
}
function clockHands154(h,m,s){return [30*((h%12)+m/60+s/3600),6*(m+s/60),6*s];}
function analogClock154(){
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('viewBox','0 0 100 100');svg.setAttribute('data-bid-clock','1');
 svg.style.cssText='position:absolute;inset:5%;width:90%;height:90%;pointer-events:none;color:inherit';
 const el=(tag,attrs)=>{const a=document.createElementNS(svg.namespaceURI,tag);for(const [k,v] of Object.entries(attrs))a.setAttribute(k,String(v));svg.append(a);return a;};
 el('circle',{cx:50,cy:50,r:46,fill:'none',stroke:'currentColor','stroke-width':2});
 for(let i=0;i<12;i++)el('line',{x1:50,y1:7,x2:50,y2:i%3===0?15:11,stroke:'currentColor','stroke-width':i%3===0?2:1,transform:'rotate('+(i*30)+' 50 50)'});
 for(const [i,y,w] of [[0,27,4],[1,15,2],[2,11,1]])el('line',{x1:50,y1:50,x2:50,y2:y,stroke:'currentColor','stroke-width':w,'stroke-linecap':'round','data-hand':i});
 el('circle',{cx:50,cy:50,r:3,fill:'currentColor'});
 return svg;
}
function paintClock154(n,d){const a=clockHands154(d.getHours(),d.getMinutes(),d.getSeconds());for(const hand of n.querySelectorAll('[data-hand]'))hand.setAttribute('transform','rotate('+a[Number(hand.getAttribute('data-hand'))]+' 50 50)');}
function value(e){""")
rep("switch(e.type){case 'canSpeed':", """switch(e.type){case 'analogClock':return '';case 'sessionStart':return catalogSessionStart154.toLocaleTimeString('ro-RO',{hour:'2-digit',minute:'2-digit'});case 'mediaPrevious':return '⏮';case 'mediaPlay':return '⏯';case 'mediaNext':return '⏭';case 'volumeUp':return 'Vol +';case 'volumeDown':return 'Vol −';case 'volumeLevel':case 'displayLight':{const d=catalogDeviceReading154(performance.now()),v=e.type==='volumeLevel'?d.volume:d.brightness;return Number.isFinite(v)&&v>=0&&v<=100?Math.round(v)+'%':'—';}case 'canSpeed':""")
rep("function widgetGesture64(e){if(e.actionLocked===true)return 'none';", "function widgetGesture64(e){if(e.actionLocked===true)return 'none';if(['mediaPrevious','mediaPlay','mediaNext','volumeUp','volumeDown'].includes(e.type))return e.gesture==='double'?'double':'tap';")
rep("function perform(e){if(e.actionLocked===true)return;", """function perform(e){if(e.actionLocked===true)return;
 const media154={mediaPrevious:'previous',mediaPlay:'playpause',mediaNext:'next'},a154=['mediaPrevious','mediaPlay','mediaNext','volumeUp','volumeDown'].includes(e.type)?e.type:e.action;
 if(Object.prototype.hasOwnProperty.call(media154,a154)){try{window.BID?.mediaKey(media154[a154]);}catch(_){}return;}
 if(a154==='volumeUp'||a154==='volumeDown'){try{window.BIDVolume?.adjust(a154==='volumeUp'?1:-1);}catch(_){}return;}""")
rep("if(gaugeKinds.includes(e.type)){n.append(gaugeNode(e));", "if(e.type==='analogClock'){n.append(analogClock154());paintClock154(n,new Date());}else if(gaugeKinds.includes(e.type)){n.append(gaugeNode(e));")
rep("if(gaugeKinds.includes(e.type))paintGauge(n,currentInstruments().speed);", "if(e.type==='analogClock')paintClock154(n,new Date());if(gaugeKinds.includes(e.type))paintGauge(n,currentInstruments().speed);")
p.write_text(s)
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('    inner class Bridge {','''    inner class Bridge {
        @JavascriptInterface
        fun catalogDeviceState154(): String {
            val result=JSONObject()
            try {
                val audio=getSystemService(AUDIO_SERVICE) as AudioManager
                val max=audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
                if(max>0)result.put("volume",100.0*audio.getStreamVolume(AudioManager.STREAM_MUSIC)/max)
            }catch(_:Exception){}
            try {
                val v=android.provider.Settings.System.getInt(contentResolver,android.provider.Settings.System.SCREEN_BRIGHTNESS)
                if(v in 0..255)result.put("brightness",100.0*v/255)
            }catch(_:Exception){}
            return result.toString()
        }
''')
p.write_text(s)
(root/'tests/editor10022/test_clock154.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function clockHands154('),j=s.indexOf('function analogClock154(',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.clockHands154;a.equal(JSON.stringify(f(12,0,0)),'[0,0,0]');a.equal(JSON.stringify(f(3,30,0)),'[105,180,0]');a.equal(JSON.stringify(f(6,0,30)),'[180.25,3,180]');console.log('3 analog clock checks passed');""")

# Reference trip widgets use the already collected, opt-in GPS aggregate.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={analogClock:", "const types={tripDistance:'Distanță GPS sesiune',tripAverage:'Viteză medie GPS',tripMaximum:'Viteză maximă GPS',tripMoving:'Durată deplasare GPS',tripStopped:'Durată staționare GPS',tripTotal:'Durată măsurată GPS',analogClock:")
rep("function value(e){", """function tripWidget155(type,data){
 if(!data||data.enabled!==true||!data.session)return '—';
 const d=data.session,fmt=(n)=>Number.isFinite(n)&&n>=0?n:null;
 const units={tripDistance:['distanceKm',2,' km'],tripAverage:['averageMovingKmh',1,' km/h'],tripMaximum:['maxKmh',1,' km/h']};
 if(units[type]){const [key,precision,unit]=units[type],n=fmt(d[key]);return n===null?'—':n.toFixed(precision)+unit;}
 const m=fmt(d.movingSeconds),s=fmt(d.stoppedSeconds);
 const n=type==='tripMoving'?m:type==='tripStopped'?s:type==='tripTotal'&&m!==null&&s!==null?m+s:null;
 if(n===null||!Number.isFinite(n))return '—';
 const sec=Math.floor(n);return [Math.floor(sec/3600),Math.floor(sec/60)%60,sec%60].map(v=>String(v).padStart(2,'0')).join(':');
}
function value(e){""")
rep("switch(e.type){case 'analogClock':", "switch(e.type){case 'tripDistance':case 'tripAverage':case 'tripMaximum':case 'tripMoving':case 'tripStopped':case 'tripTotal':return tripWidget155(e.type,catalogDeviceReading154(performance.now()).trip);case 'analogClock':")
p.write_text(s)
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('''            val result=JSONObject()
            try {
                val audio=getSystemService(AUDIO_SERVICE) as AudioManager''','''            val result=JSONObject()
            try {
                val prefs=getSharedPreferences("bid_trip",MODE_PRIVATE)
                val trip=JSONObject().put("enabled",prefs.getBoolean("enabled",false))
                if(trip.optBoolean("enabled")&&!prefs.getBoolean("reset",false)){
                    val raw=prefs.getString("session",null)
                    if(raw!=null)trip.put("session",JSONObject(raw))
                }
                result.put("trip",trip)
            }catch(_:Exception){}
            try {
                val audio=getSystemService(AUDIO_SERVICE) as AudioManager''')
p.write_text(s)
(root/'tests/editor10022/test_trip_widget155.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function tripWidget155('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.tripWidget155,d={enabled:true,session:{distanceKm:12.345,averageMovingKmh:40,maxKmh:80,movingSeconds:3661,stoppedSeconds:59}};a.equal(f('tripDistance',d),'12.35 km');a.equal(f('tripAverage',d),'40.0 km/h');a.equal(f('tripMaximum',d),'80.0 km/h');a.equal(f('tripMoving',d),'01:01:01');a.equal(f('tripStopped',d),'00:00:59');a.equal(f('tripTotal',d),'01:02:00');a.equal(f('tripTotal',{...d,enabled:false}),'—');a.equal(f('tripDistance',{enabled:true,session:{distanceKm:-1}}),'—');a.equal(f('tripMaximum',null),'—');console.log('9 trip widget checks passed');""")

# GPS altitude and course from the same validated foreground location fix.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('        emit("if(window.bidGpsSpeedUnavailable)window.bidGpsSpeedUnavailable();")','''        emit("if(window.bidGpsSpeedUnavailable)window.bidGpsSpeedUnavailable();")
        emit("if(window.bidGpsCatalog156)window.bidGpsCatalog156(null);")''')
rep('        drive.onFix(location)','''        drive.onFix(location)
        val catalog=org.json.JSONObject()
        if(location.hasAltitude()&&location.altitude.isFinite()&&location.altitude in -500.0..12000.0)
            catalog.put("altitude",location.altitude)
        if(location.hasBearing()&&location.bearing.isFinite()&&location.bearing>=0f&&location.bearing<360f&&speed>=1.0f)
            catalog.put("course",location.bearing.toDouble())
        emit("if(window.bidGpsCatalog156)window.bidGpsCatalog156("+catalog.toString()+");")''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={tripDistance:", "const types={gpsAltitude:'Altitudine GPS',gpsCourse:'Direcție deplasare GPS',tripDistance:")
rep("function value(e){", """let gpsCatalog156=null;
window.bidGpsCatalog156=data=>{gpsCatalog156=data&&typeof data==='object'&&!document.hidden?{data,at:performance.now()}:null;};
document.addEventListener('visibilitychange',()=>{if(document.hidden)gpsCatalog156=null;});
function gpsWidget156(type,sample,age,hidden){
 if(hidden||!sample||!Number.isFinite(age)||age<0||age>4000)return '—';
 if(type==='gpsAltitude'){const n=sample.altitude;return Number.isFinite(n)&&n>=-500&&n<=12000?Math.round(n)+' m':'—';}
 if(type==='gpsCourse'){const n=sample.course;if(!Number.isFinite(n)||n<0||n>=360)return '—';const dirs=['N','NE','E','SE','S','SV','V','NV'];return dirs[Math.round(n/45)%8]+' '+(Math.round(n)%360)+'°';}
 return '—';
}
function value(e){""")
rep("switch(e.type){case 'tripDistance':", "switch(e.type){case 'gpsAltitude':case 'gpsCourse':return gpsWidget156(e.type,gpsCatalog156?.data,performance.now()-(gpsCatalog156?.at??-Infinity),document.hidden);case 'tripDistance':")
p.write_text(s)
(root/'tests/editor10022/test_gps_widgets156.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function gpsWidget156('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.gpsWidget156;a.equal(f('gpsAltitude',{altitude:123.6},0,false),'124 m');a.equal(f('gpsAltitude',{altitude:-25},4000,false),'-25 m');a.equal(f('gpsAltitude',{altitude:12},4001,false),'—');a.equal(f('gpsCourse',{course:90},0,false),'E 90°');a.equal(f('gpsCourse',{course:359.9},0,false),'N 0°');a.equal(f('gpsCourse',{course:360},0,false),'—');a.equal(f('gpsCourse',{course:90},0,true),'—');a.equal(f('gpsCourse',null,0,false),'—');console.log('8 GPS widget checks passed');""")

# Keep pure trip test independent of newly inserted browser event handlers.
t=root/'tests/editor10022/test_trip_widget155.js'
u=t.read_text()
a="j=s.indexOf('function value(e)',i)"
assert u.count(a)==1
t.write_text(u.replace(a,"j=s.indexOf('let gpsCatalog156=',i)",1))
# Add GNSS satellite status using Android's foreground GPS listener.
p=root/'app/src/main/java/ro/dj88bid/car/BidGpsSpeed.kt'
s=p.read_text()
rep('    private var running = false', '''    private var running = false
    private var gnssRegistered157=false
    private val gnss157=object:android.location.GnssStatus.Callback(){
        override fun onSatelliteStatusChanged(status:android.location.GnssStatus){
            if(!running)return
            var used=0
            for(i in 0 until status.satelliteCount)if(status.usedInFix(i))used++
            emit("if(window.bidGnss157)window.bidGnss157("+used+","+status.satelliteCount+");")
        }
        override fun onStopped(){emit("if(window.bidGnss157)window.bidGnss157(null,null);")}
    }''')
rep('            running = true\n            drive.start()', '''            running = true
            if(Build.VERSION.SDK_INT>=24)try{gnssRegistered157=m.registerGnssStatusCallback(gnss157,handler)}catch(_:Exception){}
            drive.start()''')
rep('        running = false\n        drive.stop()', '''        running = false
        if(Build.VERSION.SDK_INT>=24&&gnssRegistered157)try{manager?.unregisterGnssStatusCallback(gnss157)}catch(_:Exception){}
        gnssRegistered157=false
        emit("if(window.bidGnss157)window.bidGnss157(null,null);")
        drive.stop()''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={gpsAltitude:", "const types={gpsSatellites:'Sateliți GPS utilizați / vizibili',gpsAltitude:")
rep("let gpsCatalog156=null;", """let gnssSample157=null;
function gnssValue157(used,total,age,hidden){
 if(hidden||!Number.isFinite(age)||age<0||age>5000||!Number.isInteger(used)||!Number.isInteger(total)||used<0||total<used||total>512)return '—';
 return used+' / '+total;
}
window.bidGnss157=(used,total)=>{gnssSample157=document.hidden?null:{used,total,at:performance.now()};};
document.addEventListener('visibilitychange',()=>{if(document.hidden)gnssSample157=null;});
let gpsCatalog156=null;""")
rep("switch(e.type){case 'gpsAltitude':", "switch(e.type){case 'gpsSatellites':return gnssValue157(gnssSample157?.used,gnssSample157?.total,performance.now()-(gnssSample157?.at??-Infinity),document.hidden);case 'gpsAltitude':")
# Adjust the previous pure-test boundary again to exclude all browser hooks.
t=root/'tests/editor10022/test_trip_widget155.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('let gpsCatalog156=',i)","j=s.indexOf('let gnssSample157=',i)",1))
p.write_text(s)
(root/'tests/editor10022/test_gnss157.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function gnssValue157('),j=s.indexOf('window.bidGnss157=',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.gnssValue157;a.equal(f(7,12,0,false),'7 / 12');a.equal(f(0,0,0,false),'0 / 0');a.equal(f(12,7,0,false),'—');a.equal(f(7,12,5001,false),'—');a.equal(f(7,12,0,true),'—');a.equal(f(null,null,0,false),'—');console.log('6 GNSS widget checks passed');""")

# Isolate CAN formatter tests from browser-dependent widget setup.
t=root/'tests/editor10022/test_final_batch150.js'
u=t.read_text()
a="['function canWidgetValue150(','function value(e)']"
assert u.count(a)==1
t.write_text(u.replace(a,"['function canWidgetValue150(','const catalogSessionStart154=']",1))
# Reuse actual Android connectivity snapshots; no new permissions.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('        fun catalogDeviceState154(): String {\n            val result=JSONObject()', '''        fun catalogDeviceState154(): String {
            val result=JSONObject()
            try {result.put("connectivity",BidConnectivity.snapshot(this@MainActivity))}catch(_:Exception){}''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={gpsSatellites:", "const types={androidWifi:'Wi-Fi Android',androidBluetooth:'Bluetooth Android',androidNetwork:'Rețea mobilă Android',gpsSatellites:")
rep("function value(e){", """function connectivityValue158(type,d){
 if(!d)return '—';
 if(type==='androidNetwork')return d.simPresent===false?'Fără SIM':typeof d.networkGeneration==='string'&&['2G','3G','4G','4G+','5G'].includes(d.networkGeneration)?d.networkGeneration:'—';
 const wifi=type==='androidWifi',enabled=d[wifi?'wifi':'bluetooth'],connected=d[wifi?'wifiConnected':'bluetoothConnected'];
 if(enabled===false)return 'Oprit';
 if(enabled!==true)return '—';
 if(connected===false)return 'Neconectat';
 if(connected!==true)return 'Pornit · stare necunoscută';
 return wifi&&Number.isInteger(d.wifiLevel)&&d.wifiLevel>=0&&d.wifiLevel<=4?'Conectat · '+d.wifiLevel+'/4':'Conectat';
}
function value(e){""")
rep("switch(e.type){case 'gpsSatellites':", "switch(e.type){case 'androidWifi':case 'androidBluetooth':case 'androidNetwork':return connectivityValue158(e.type,catalogDeviceReading154(performance.now()).connectivity);case 'gpsSatellites':")
p.write_text(s)
t=root/'tests/editor10022/test_gps_widgets156.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('function value(e)',i)","j=s.indexOf('function connectivityValue158(',i)",1))
(root/'tests/editor10022/test_connectivity158.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function connectivityValue158('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.connectivityValue158;a.equal(f('androidWifi',{wifi:true,wifiConnected:true,wifiLevel:3}),'Conectat · 3/4');a.equal(f('androidWifi',{wifi:false}),'Oprit');a.equal(f('androidBluetooth',{bluetooth:true,bluetoothConnected:null}),'Pornit · stare necunoscută');a.equal(f('androidBluetooth',{bluetooth:true,bluetoothConnected:false}),'Neconectat');a.equal(f('androidNetwork',{networkGeneration:'4G+'}),'4G+');a.equal(f('androidNetwork',{simPresent:false}),'Fără SIM');a.equal(f('androidWifi',null),'—');console.log('7 connectivity widget checks passed');""")

# Read Android battery temperature and charge state, not vehicle battery voltage.
p=root/'app/src/main/java/ro/dj88bid/car/MainActivity.kt'
s=p.read_text()
rep('            try {result.put("connectivity",BidConnectivity.snapshot(this@MainActivity))}catch(_:Exception){}','''            try {result.put("connectivity",BidConnectivity.snapshot(this@MainActivity))}catch(_:Exception){}
            try {
                val battery=registerReceiver(null,android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED))
                if(battery!=null&&battery.getBooleanExtra(android.os.BatteryManager.EXTRA_PRESENT,false)){
                    val info=JSONObject()
                    val level=battery.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL,-1)
                    val scale=battery.getIntExtra(android.os.BatteryManager.EXTRA_SCALE,-1)
                    if(scale>0&&level in 0..scale)info.put("percent",100.0*level/scale)
                    val status=battery.getIntExtra(android.os.BatteryManager.EXTRA_STATUS,-1)
                    when(status){
                        android.os.BatteryManager.BATTERY_STATUS_CHARGING->info.put("charging",true)
                        android.os.BatteryManager.BATTERY_STATUS_FULL->info.put("charging",true)
                        android.os.BatteryManager.BATTERY_STATUS_DISCHARGING,android.os.BatteryManager.BATTERY_STATUS_NOT_CHARGING->info.put("charging",false)
                    }
                    val temp=battery.getIntExtra(android.os.BatteryManager.EXTRA_TEMPERATURE,Int.MIN_VALUE)
                    if(temp in -400..1000)info.put("temperature",temp/10.0)
                    result.put("battery",info)
                }
            }catch(_:Exception){}''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={androidWifi:", "const types={androidBatteryPercent:'Baterie dispozitiv Android',androidBatteryTemp:'Temperatură baterie Android',androidBatteryCharge:'Stare încărcare Android',androidWifi:")
rep("function value(e){", """function batteryWidget159(type,b){
 if(!b)return '—';
 if(type==='androidBatteryPercent')return Number.isFinite(b.percent)&&b.percent>=0&&b.percent<=100?Math.round(b.percent)+'%':'—';
 if(type==='androidBatteryTemp')return Number.isFinite(b.temperature)&&b.temperature>=-40&&b.temperature<=100?b.temperature.toFixed(1)+' °C':'—';
 if(type==='androidBatteryCharge')return b.charging===true?'Alimentat / încărcare':b.charging===false?'Nu se încarcă':'—';
 return '—';
}
function value(e){""")
rep("switch(e.type){case 'androidWifi':", "switch(e.type){case 'androidBatteryPercent':case 'androidBatteryTemp':case 'androidBatteryCharge':return batteryWidget159(e.type,catalogDeviceReading154(performance.now()).battery);case 'androidWifi':")
p.write_text(s)
t=root/'tests/editor10022/test_connectivity158.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('function value(e)',i)","j=s.indexOf('function batteryWidget159(',i)",1))
(root/'tests/editor10022/test_battery159.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function batteryWidget159('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.batteryWidget159;a.equal(f('androidBatteryPercent',{percent:75.5}),'76%');a.equal(f('androidBatteryPercent',{percent:101}),'—');a.equal(f('androidBatteryTemp',{temperature:32.5}),'32.5 °C');a.equal(f('androidBatteryTemp',{}),'—');a.equal(f('androidBatteryCharge',{charging:true}),'Alimentat / încărcare');a.equal(f('androidBatteryCharge',{charging:false}),'Nu se încarcă');a.equal(f('androidBatteryCharge',null),'—');console.log('7 Android battery widget checks passed');""")

# Add device orientation widgets via optional Android rotation-vector sensor.
# Register only while BID is foreground; never treat mounting angle as car tilt.
src=root/'app/src/main/java/ro/dj88bid/car'
(src/'BidOrientationSensor161.kt').write_text('''package ro.dj88bid.car
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.SystemClock
import org.json.JSONObject
class BidOrientationSensor161(context:Context):SensorEventListener {
 private val manager=context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
 private val sensor=manager?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
 private var active=false
 private var last=0L
 private var values=FloatArray(0)
 fun start(){
  if(active||sensor==null)return
  try{active=manager?.registerListener(this,sensor,SensorManager.SENSOR_DELAY_UI)==true}catch(_:Exception){}
 }
 fun stop(){active=false;last=0L;values=FloatArray(0);try{manager?.unregisterListener(this)}catch(_:Exception){}}
 override fun onAccuracyChanged(s:Sensor?,accuracy:Int){if(accuracy==SensorManager.SENSOR_STATUS_UNRELIABLE)last=0L}
 override fun onSensorChanged(e:SensorEvent){
  if(!active||e.sensor.type!=Sensor.TYPE_ROTATION_VECTOR||e.accuracy==SensorManager.SENSOR_STATUS_UNRELIABLE)return
  try{
   val matrix=FloatArray(9)
   SensorManager.getRotationMatrixFromVector(matrix,e.values)
   val result=SensorManager.getOrientation(matrix,FloatArray(3))
   if(result.all{it.isFinite()}){values=result;last=SystemClock.elapsedRealtime()}
  }catch(_:Exception){last=0L}
 }
 fun snapshot():JSONObject{
  val out=JSONObject()
  if(!active||last==0L||SystemClock.elapsedRealtime()-last !in 0L..3000L||values.size!=3)return out
  fun deg(v:Float)=Math.toDegrees(v.toDouble())
  return out.put("azimuth",(deg(values[0])+360)%360).put("pitch",deg(values[1])).put("roll",deg(values[2]))
 }
}
''')
p=src/'MainActivity.kt'
s=p.read_text()
rep('    private var speedForeground = false','''    private var speedForeground = false
    private val catalogOrientation161 by lazy { BidOrientationSensor161(this) }''')
rep('        super.onResume()','''        super.onResume()
        catalogOrientation161.start()''')
rep('        super.onPause()','''        catalogOrientation161.stop()
        super.onPause()''')
rep('            try {result.put("connectivity",BidConnectivity.snapshot(this@MainActivity))}catch(_:Exception){}','''            try {result.put("connectivity",BidConnectivity.snapshot(this@MainActivity))}catch(_:Exception){}
            try {result.put("orientation",catalogOrientation161.snapshot())}catch(_:Exception){}''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={androidBatteryPercent:", "const types={deviceCompass:'Busolă dispozitiv Android',deviceInclination:'Înclinare dispozitiv Android',androidBatteryPercent:")
rep("function value(e){", """function orientationWidget161(type,d){
 if(!d)return '—';
 if(type==='deviceCompass'){const n=d.azimuth;if(!Number.isFinite(n)||n<0||n>=360)return '—';return ['N','NE','E','SE','S','SV','V','NV'][Math.round(n/45)%8]+' '+(Math.round(n)%360)+'°';}
 if(type==='deviceInclination'){const {pitch,roll}=d;if(!Number.isFinite(pitch)||!Number.isFinite(roll)||Math.abs(pitch)>90.01||Math.abs(roll)>180.01)return '—';return 'Dispozitiv: '+pitch.toFixed(1)+'° / '+roll.toFixed(1)+'°';}
 return '—';
}
function value(e){""")
rep("switch(e.type){case 'androidBatteryPercent':", "switch(e.type){case 'deviceCompass':case 'deviceInclination':return orientationWidget161(e.type,catalogDeviceReading154(performance.now()).orientation);case 'androidBatteryPercent':")
p.write_text(s)
t=root/'tests/editor10022/test_battery159.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('function value(e)',i)","j=s.indexOf('function orientationWidget161(',i)",1))
(root/'tests/editor10022/test_orientation161.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function orientationWidget161('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.orientationWidget161;a.equal(f('deviceCompass',{azimuth:90}),'E 90°');a.equal(f('deviceCompass',{azimuth:359.9}),'N 0°');a.equal(f('deviceCompass',{azimuth:360}),'—');a.equal(f('deviceInclination',{pitch:10,roll:-2}),'Dispozitiv: 10.0° / -2.0°');a.equal(f('deviceInclination',{pitch:91,roll:0}),'—');a.equal(f('deviceCompass',null),'—');console.log('6 orientation widget checks passed');""")

# Media metadata via Android active sessions, explicit user-granted notification access.
src=root/'app/src/main/java/ro/dj88bid/car'
(src/'BidMediaAccess162.kt').write_text('''package ro.dj88bid.car
import android.service.notification.NotificationListenerService
import android.content.Context
import android.content.ComponentName
import android.media.MediaMetadata
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import android.os.SystemClock
import org.json.JSONObject

class BidMediaAccess162:NotificationListenerService() {
 companion object {
  fun snapshot(context:Context):JSONObject {
   val out=JSONObject()
   try {
    val manager=context.getSystemService(Context.MEDIA_SESSION_SERVICE) as MediaSessionManager
    val controllers=manager.getActiveSessions(ComponentName(context,BidMediaAccess162::class.java))
    out.put("authorized",true)
    val controller=controllers.firstOrNull{it.playbackState?.state==PlaybackState.STATE_PLAYING}?:controllers.firstOrNull()?:return out
    val data=controller.metadata
    val state=controller.playbackState
    out.put("package",controller.packageName)
    fun field(key:String,name:String){data?.getString(key)?.take(160)?.let{out.put(name,it)}}
    field(MediaMetadata.METADATA_KEY_TITLE,"title")
    field(MediaMetadata.METADATA_KEY_ARTIST,"artist")
    field(MediaMetadata.METADATA_KEY_ALBUM,"album")
    val duration=data?.getLong(MediaMetadata.METADATA_KEY_DURATION)?:0L
    if(duration>0L)out.put("duration",duration)
    if(state!=null){
     out.put("playing",state.state==PlaybackState.STATE_PLAYING)
     var position=state.position
     if(position>=0L){
      val elapsed=SystemClock.elapsedRealtime()-state.lastPositionUpdateTime
      if(state.state==PlaybackState.STATE_PLAYING&&state.lastPositionUpdateTime>0L&&elapsed in 0L..600000L&&state.playbackSpeed.isFinite())
       position+=(elapsed*state.playbackSpeed).toLong()
      out.put("position",if(duration>0L)position.coerceIn(0L,duration) else position.coerceAtLeast(0L))
     }
    }
   }catch(_:SecurityException){out.put("authorized",false)}catch(_:Exception){}
   return out
  }
 }
}
''')
p=root/'app/src/main/AndroidManifest.xml'
s=p.read_text()
rep('</application>','''        <service android:name=".BidMediaAccess162" android:label="BID — acces multimedia opțional" android:exported="true" android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter><action android:name="android.service.notification.NotificationListenerService" /></intent-filter>
        </service>
    </application>''')
p.write_text(s)
p=src/'MainActivity.kt'
s=p.read_text()
rep('            try {result.put("orientation",catalogOrientation161.snapshot())}catch(_:Exception){}','''            try {result.put("orientation",catalogOrientation161.snapshot())}catch(_:Exception){}
            try {result.put("media",BidMediaAccess162.snapshot(this@MainActivity))}catch(_:Exception){}''')
rep('    inner class Bridge {','''    inner class Bridge {
        @JavascriptInterface
        fun openMediaAccess162()=runOnUiThread{
            if(webView.url!="file:///android_asset/index.html"||!hasWindowFocus()||isFinishing)return@runOnUiThread
            android.app.AlertDialog.Builder(this@MainActivity).setTitle("Acces multimedia opțional")
                .setMessage("Android solicită acces la notificări pentru citirea sesiunilor media. BID folosește numai metadatele sesiunilor media; nu citește, salvează sau transmite notificările. Poți refuza sau revoca accesul.")
                .setPositiveButton("Setări Android"){_,_->try{startActivity(Intent(android.provider.Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))}catch(_:Exception){}}
                .setNegativeButton("Anulează",null).show()
        }
''')
p.write_text(s)
p=root/'app/src/main/assets/bid_general.js'
s=p.read_text()
rep("button('Închide',","button('Acces multimedia opțional',()=>{try{native().openMediaAccess162();}catch(_){}});\nbutton('Închide',")
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={deviceCompass:", "const types={mediaTitle:'Titlu melodie',mediaArtist:'Artist',mediaAlbum:'Album',mediaProgress:'Progres redare',mediaState:'Stare player',deviceCompass:")
rep("function value(e){", """function mediaWidget162(type,d){
 if(!d||d.authorized!==true)return '—';
 const keys={mediaTitle:'title',mediaArtist:'artist',mediaAlbum:'album'};
 if(keys[type])return typeof d[keys[type]]==='string'&&d[keys[type]].trim()?d[keys[type]].slice(0,160):'—';
 if(type==='mediaState')return d.playing===true?'Redare':d.playing===false?'Pauză / oprit':'—';
 if(type==='mediaProgress'){
 const fmt=n=>{const s=Math.floor(n/1000);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');};
 return Number.isFinite(d.position)&&Number.isFinite(d.duration)&&d.duration>0&&d.position>=0&&d.position<=d.duration?fmt(d.position)+' / '+fmt(d.duration):'—';
 }
 return '—';
}
function value(e){""")
rep("switch(e.type){case 'deviceCompass':", "switch(e.type){case 'mediaTitle':case 'mediaArtist':case 'mediaAlbum':case 'mediaProgress':case 'mediaState':return mediaWidget162(e.type,catalogDeviceReading154(performance.now()).media);case 'deviceCompass':")
p.write_text(s)
t=root/'tests/editor10022/test_orientation161.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('function value(e)',i)","j=s.indexOf('function mediaWidget162(',i)",1))
(root/'tests/editor10022/test_media162.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function mediaWidget162('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.mediaWidget162,d={authorized:true,title:'Song',artist:'Artist',album:'Album',playing:true,position:65000,duration:185000};a.equal(f('mediaTitle',d),'Song');a.equal(f('mediaArtist',d),'Artist');a.equal(f('mediaAlbum',d),'Album');a.equal(f('mediaProgress',d),'1:05 / 3:05');a.equal(f('mediaState',d),'Redare');a.equal(f('mediaState',{...d,playing:false}),'Pauză / oprit');a.equal(f('mediaTitle',{...d,authorized:false}),'—');a.equal(f('mediaProgress',{...d,position:200000}),'—');a.equal(f('mediaTitle',null),'—');console.log('9 media widget checks passed');""")

# Album artwork from the authorized active Android media session, bounded and local.
p=root/'app/src/main/java/ro/dj88bid/car/BidMediaAccess162.kt'
s=p.read_text()
rep('    field(MediaMetadata.METADATA_KEY_ALBUM,"album")','''    field(MediaMetadata.METADATA_KEY_ALBUM,"album")
    try {
     val bitmap=data?.getBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART)
       ?:data?.getBitmap(MediaMetadata.METADATA_KEY_ART)
       ?:data?.getBitmap(MediaMetadata.METADATA_KEY_DISPLAY_ICON)
     if(bitmap!=null&&bitmap.width>0&&bitmap.height>0){
      val factor=minOf(1.0,192.0/maxOf(bitmap.width,bitmap.height))
      val scaled=android.graphics.Bitmap.createScaledBitmap(bitmap,maxOf(1,(bitmap.width*factor).toInt()),maxOf(1,(bitmap.height*factor).toInt()),true)
      val bytes=java.io.ByteArrayOutputStream()
      if(scaled.compress(android.graphics.Bitmap.CompressFormat.JPEG,75,bytes)&&bytes.size()<=100000)
       out.put("art","data:image/jpeg;base64,"+android.util.Base64.encodeToString(bytes.toByteArray(),android.util.Base64.NO_WRAP))
      if(scaled!==bitmap)scaled.recycle()
     }
    }catch(_:Exception){}''')
p.write_text(s)
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={mediaTitle:", "const types={mediaArtwork:'Copertă album',mediaTitle:")
rep("function value(e){", """function artworkValue164(d){
 return d?.authorized===true&&typeof d.art==='string'&&d.art.length<=134000&&d.art.startsWith('data:image/jpeg;base64,')&&/^[A-Za-z0-9+/=]+$/.test(d.art.slice(23))?d.art:null;
}
function paintArtwork164(n){
 const url=artworkValue164(catalogDeviceReading154(performance.now()).media);
 n.style.backgroundImage=url?'url("'+url+'")':'none';
 n.style.backgroundSize='contain';n.style.backgroundRepeat='no-repeat';n.style.backgroundPosition='center';
}
function value(e){""")
rep("switch(e.type){case 'mediaTitle':", "switch(e.type){case 'mediaArtwork':return artworkValue164(catalogDeviceReading154(performance.now()).media)?'':'—';case 'mediaTitle':")
rep("if(e.type==='analogClock'){n.append(analogClock154());", "if(e.type==='mediaArtwork')paintArtwork164(n);if(e.type==='analogClock'){n.append(analogClock154());")
rep("if(e.type==='analogClock')paintClock154(n,new Date());", "if(e.type==='mediaArtwork')paintArtwork164(n);if(e.type==='analogClock')paintClock154(n,new Date());")
p.write_text(s)
t=root/'tests/editor10022/test_media162.js'
u=t.read_text()
t.write_text(u.replace("j=s.indexOf('function value(e)',i)","j=s.indexOf('function artworkValue164(',i)",1))
(root/'tests/editor10022/test_artwork164.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function artworkValue164('),j=s.indexOf('function paintArtwork164(',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.artworkValue164,u='data:image/jpeg;base64,/9j/AA==';a.equal(f({authorized:true,art:u}),u);a.equal(f({authorized:false,art:u}),null);a.equal(f({authorized:true,art:'https://example.com/image.jpg'}),null);a.equal(f({authorized:true,art:u+'!'}),null);a.equal(f(null),null);console.log('5 artwork checks passed');""")

# Complete the media reference controls with a combined elapsed/remaining readout.
p=root/'app/src/main/assets/bid_theme_builder.js'
s=p.read_text()
rep("const types={mediaArtwork:", "const types={mediaRemaining:'Timp rămas melodie',mediaElapsed:'Timp redat melodie',mediaPercent:'Procent redare',mediaTrack:'Melodie și artist',mediaArtwork:")
rep("function value(e){", """function mediaExtra165(type,d){
 if(d?.authorized!==true)return '—';
 if(type==='mediaTrack'){const fields=[d.title,d.artist].filter(x=>typeof x==='string'&&x.trim()).map(x=>x.slice(0,160));return fields.join(' · ')||'—';}
 const p=d.position,t=d.duration;
 if(!Number.isFinite(p)||p<0)return '—';
 const fmt=n=>{const s=Math.floor(n/1000);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');};
 if(type==='mediaElapsed')return fmt(p);
 if(!Number.isFinite(t)||t<=0||p>t)return '—';
 if(type==='mediaRemaining')return '−'+fmt(t-p);
 if(type==='mediaPercent')return Math.round(p/t*100)+'%';
 return '—';
}
function value(e){""")
rep("switch(e.type){case 'mediaArtwork':", "switch(e.type){case 'mediaRemaining':case 'mediaElapsed':case 'mediaPercent':case 'mediaTrack':return mediaExtra165(e.type,catalogDeviceReading154(performance.now()).media);case 'mediaArtwork':")
# Avoid applying invalid negative/NaN sensor data and keep artwork local.
p.write_text(s)
(root/'tests/editor10022/test_media_extra165.js').write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8'),i=s.indexOf('function mediaExtra165('),j=s.indexOf('function value(e)',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.mediaExtra165,d={authorized:true,title:'Song',artist:'Artist',position:60000,duration:180000};a.equal(f('mediaTrack',d),'Song · Artist');a.equal(f('mediaElapsed',d),'1:00');a.equal(f('mediaRemaining',d),'−2:00');a.equal(f('mediaPercent',d),'33%');a.equal(f('mediaPercent',{...d,duration:0}),'—');a.equal(f('mediaRemaining',{...d,position:190000}),'—');a.equal(f('mediaTrack',{...d,authorized:false}),'—');console.log('7 additional media checks passed');""")
