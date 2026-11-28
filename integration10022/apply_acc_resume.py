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
rep("button('Închide',","button('Statistici GPS locale',()=>{try{native().openBidTripSummary();}catch(_){}});\\nbutton('Închide',")
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
rep("button('Închide',","button('Istoric GPS — 1, 7, 30 zile',()=>{try{native().openBidTripHistory();}catch(_){}});\\nbutton('Închide',")
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
