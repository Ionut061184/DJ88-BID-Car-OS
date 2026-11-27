package ro.dj88bid.car
import android.app.Activity
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject
import java.net.URL
import javax.net.ssl.HttpsURLConnection
import java.security.MessageDigest
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicBoolean
class BidOnlineCatalog(private val activity: Activity, private val web: WebView) {
 private val busy=AtomicBoolean(false)
 private val base="https://raw.githubusercontent.com/Ionut061184/DJ88-BID-Car-OS/main/theme-catalog/"
 @JavascriptInterface fun request(token:String,id:String,sha:String,size:Int) {
  if(!token.matches(Regex("[0-9]{1,12}"))) return
  activity.runOnUiThread {
   if(web.url!="file:///android_asset/index.html"||activity.isFinishing||!activity.hasWindowFocus()) return@runOnUiThread
   val isIndex=id.isEmpty()
   if(!isIndex&&(!id.matches(Regex("[-a-zA-Z0-9_]{1,64}"))||!sha.matches(Regex("[a-f0-9]{64}"))||size !in 1..4000000)){emit(token,false,"Cerere invalidă","");return@runOnUiThread}
   if(!busy.compareAndSet(false,true)){emit(token,false,"O descărcare este deja activă","");return@runOnUiThread}
   Thread {
    var connection:HttpsURLConnection?=null
    try {
     val c=URL(base+if(isIndex) "index.json" else "themes/$id.json").openConnection() as HttpsURLConnection
     connection=c;c.instanceFollowRedirects=false;c.connectTimeout=10000;c.readTimeout=10000
     val limit=if(isIndex)128000 else size
     if(c.responseCode!=200||c.contentLengthLong>limit)throw IllegalStateException()
     val bytes=c.inputStream.use{input->val out=ByteArrayOutputStream();val b=ByteArray(8192);while(true){val n=input.read(b);if(n<0)break;if(out.size()+n>limit)throw IllegalStateException();out.write(b,0,n)};out.toByteArray()}
     if(!isIndex){val actual=MessageDigest.getInstance("SHA-256").digest(bytes).joinToString(""){"%02x".format(it.toInt() and 255)};if(bytes.size!=size||actual!=sha)throw IllegalStateException()}
     emit(token,true,"",String(bytes,Charsets.UTF_8))
    }catch(e:Exception){emit(token,false,"Catalog indisponibil sau verificare eșuată","")}finally{connection?.disconnect();busy.set(false)}
   }.start()
  }
 }
 private fun emit(token:String,ok:Boolean,message:String,data:String){val json=JSONObject().put("token",token).put("ok",ok).put("message",message).put("data",data).toString();activity.runOnUiThread{if(!activity.isFinishing&&web.url=="file:///android_asset/index.html")web.evaluateJavascript("if(window.bidOnlineCatalogResult)window.bidOnlineCatalogResult("+json+");",null)}}
}