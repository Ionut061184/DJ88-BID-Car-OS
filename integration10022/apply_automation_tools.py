from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
s=p.read_text()
anchor="    inner class Bridge {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    inner class Bridge {
        @JavascriptInterface
        fun openAutomationTool(provider: String) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            val pkg = when(provider) {
                "tasker" -> "net.dinglisch.android.taskerm"
                "macrodroid" -> "com.arlosoft.macrodroid"
                "automate" -> "com.llamalab.automate"
                else -> return@runOnUiThread
            }
            val launch = packageManager.getLaunchIntentForPackage(pkg)
            try {
                if (launch != null) startActivity(launch)
                else android.widget.Toast.makeText(this@MainActivity,"Instrumentul nu este instalat",android.widget.Toast.LENGTH_SHORT).show()
            } catch (_: Exception) {
                android.widget.Toast.makeText(this@MainActivity,"Instrument indisponibil",android.widget.Toast.LENGTH_SHORT).show()
            }
        }
''',1)
p.write_text(s)
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
anchor="button('Închide',"
assert s.count(anchor)==1
s=s.replace(anchor,"for(const [id,label] of [['tasker','Tasker'],['macrodroid','MacroDroid'],['automate','Automate']])button(label+' — deschide configurarea',()=>{try{native().openAutomationTool(id);}catch(_){}});\n"+anchor,1)
p.write_text(s)
