from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
s=p.read_text()
anchor="    inner class Bridge {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    inner class Bridge {
        @JavascriptInterface
        fun taskerEventsEnabled(): Boolean = getSharedPreferences("bid_tasker_events", MODE_PRIVATE).getBoolean("enabled", false)

        @JavascriptInterface
        fun setTaskerEventsEnabled(enabled: Boolean) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            getSharedPreferences("bid_tasker_events", MODE_PRIVATE).edit().putBoolean("enabled",enabled).apply()
        }

        @JavascriptInterface
        fun emitTaskerEvent(event: String) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            if (event !in setOf("editor_open", "editor_closed", "manual_test")) return@runOnUiThread
            if (!getSharedPreferences("bid_tasker_events", MODE_PRIVATE).getBoolean("enabled",false)) return@runOnUiThread
            sendBroadcast(Intent("ro.dj88bid.car.EVENT").setPackage("net.dinglisch.android.taskerm").putExtra("bid_event",event))
        }
''',1)
p.write_text(s)
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
anchor="button('Închide',"
assert s.count(anchor)==1
s=s.replace(anchor,"""const taskerEvents=document.createElement('label');
const eventToggle=document.createElement('input');eventToggle.type='checkbox';
try{eventToggle.checked=native().taskerEventsEnabled()===true;}catch(_){}
eventToggle.onchange=()=>{try{native().setTaskerEventsEnabled(eventToggle.checked);}catch(_){eventToggle.checked=false;}};
taskerEvents.append(eventToggle,document.createTextNode(' Trimite evenimente BID către Tasker'));modal.append(taskerEvents);
button('Testează eveniment Tasker',()=>{try{native().emitTaskerEvent('manual_test');}catch(_){}});
const eventHelp=document.createElement('p');eventHelp.textContent='În Tasker: Event → Intent Received; Action: ro.dj88bid.car.EVENT. Extra: bid_event. Test manual; nu confirmă recepția.';modal.append(eventHelp);
"""+anchor,1)
p.write_text(s)
