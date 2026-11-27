from pathlib import Path
import sys
root=Path(sys.argv[1])
k=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
s=k.read_text()
anchor="    inner class Bridge {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    inner class Bridge {
        @JavascriptInterface
        fun openExternalMap(provider: String) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            val pkg = when(provider) {
                "yandex" -> "ru.yandex.yandexmaps"
                "baidu" -> "com.baidu.BaiduMap"
                else -> return@runOnUiThread
            }
            try {
                val launch = packageManager.getLaunchIntentForPackage(pkg)
                if (launch != null) startActivity(launch)
                else android.widget.Toast.makeText(this@MainActivity,"Aplicația de hărți nu este instalată",android.widget.Toast.LENGTH_SHORT).show()
            } catch (_: Exception) {
                android.widget.Toast.makeText(this@MainActivity,"Hartă externă indisponibilă",android.widget.Toast.LENGTH_SHORT).show()
            }
        }
''',1)
k.write_text(s)
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
anchor="button('Închide',"
assert s.count(anchor)==1
s=s.replace(anchor,"button('Yandex Maps — aplicație externă',()=>{try{native().openExternalMap('yandex');}catch(_){}});\nbutton('Baidu Maps — aplicație externă',()=>{try{native().openExternalMap('baidu');}catch(_){}});\n"+anchor,1)
p.write_text(s)
