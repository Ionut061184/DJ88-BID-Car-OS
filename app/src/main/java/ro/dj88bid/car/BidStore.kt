package ro.dj88bid.car
import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.webkit.JavascriptInterface
import android.webkit.WebView
class BidStore(private val activity: Activity, private val web: WebView) {
 @JavascriptInterface fun open(kind: String) {
  val query = when(kind) { "icons" -> "icon pack"; "themes" -> "DJ88 BID theme"; else -> return }
  activity.runOnUiThread {
   if(web.url != "file:///android_asset/index.html" || !activity.hasWindowFocus() || activity.isFinishing) return@runOnUiThread
   val market=Intent(Intent.ACTION_VIEW,Uri.parse("market://search?q="+Uri.encode(query)+"&c=apps")).setPackage("com.android.vending")
   try { activity.startActivity(market) } catch (_: Exception) {
    try { activity.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse("https://play.google.com/store/search?q="+Uri.encode(query)+"&c=apps"))) }
    catch (_: Exception) { android.widget.Toast.makeText(activity,"Magazin indisponibil",android.widget.Toast.LENGTH_SHORT).show() }
   }
  }
 }
}