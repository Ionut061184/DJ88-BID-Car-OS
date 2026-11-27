package ro.dj88bid.car
import android.app.Activity
import android.content.Context
import android.media.AudioManager
import android.os.SystemClock
import android.webkit.JavascriptInterface
import android.webkit.WebView
class BidVolume(private val activity: Activity, private val web: WebView) {
 private var last = -1000L
 private fun audio() = activity.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
 @JavascriptInterface fun available(): Boolean = try { audio()?.let { !it.isVolumeFixed } ?: false } catch (_: Exception) { false }
 @JavascriptInterface fun adjust(direction: Int) {
  if(direction != 1 && direction != -1) return
  activity.runOnUiThread {
   if(web.url != "file:///android_asset/index.html" || !activity.hasWindowFocus() || activity.isFinishing) return@runOnUiThread
   val now = SystemClock.elapsedRealtime()
   if(now-last<350) return@runOnUiThread
   val manager=audio() ?: return@runOnUiThread
   if(manager.isVolumeFixed) return@runOnUiThread
   last=now
   try { manager.adjustStreamVolume(AudioManager.STREAM_MUSIC,if(direction==1) AudioManager.ADJUST_RAISE else AudioManager.ADJUST_LOWER,AudioManager.FLAG_SHOW_UI) } catch (_: SecurityException) {}
  }
 }
}