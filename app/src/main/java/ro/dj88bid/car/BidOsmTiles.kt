package ro.dj88bid.car

import android.app.Activity
import android.net.http.HttpResponseCache
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** On-demand map tiles only. No prefetch, no offline region downloads. */
class BidOsmTiles(private val activity:Activity,private val web:WebView) {
    @Volatile private var enabled=false
    @Volatile private var foreground=false
    @Volatile private var blockedUntil=0L
    private var cacheReady=false
    init {
        try {
            if(HttpResponseCache.getInstalled()==null)HttpResponseCache.install(File(activity.cacheDir,"bid_http_tiles"),40L*1024*1024)
            cacheReady=HttpResponseCache.getInstalled()!=null
        } catch (_:Exception) {}
    }
    fun start(){foreground=true}
    fun stop(){foreground=false;try{HttpResponseCache.getInstalled()?.flush()}catch(_:Exception){}}
    @JavascriptInterface fun enable(value:Boolean)=activity.runOnUiThread{
        if(web.url=="file:///android_asset/index.html")enabled=value
    }
    private fun response(code:Int,reason:String)=WebResourceResponse("text/plain","UTF-8",code,reason,mapOf("Cache-Control" to "no-store"),ByteArrayInputStream(ByteArray(0)))
    fun intercept(request:WebResourceRequest):WebResourceResponse?{
        val uri=request.url
        if(uri.host!="bid-osm.invalid")return null
        if(uri.scheme!="https"||request.method!="GET"||!enabled||!foreground||!cacheReady)return response(403,"Disabled")
        val m=Regex("^/([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6})[.]png$").matchEntire(uri.path?:"")?:return response(400,"Bad request")
        val z=m.groupValues[1].toInt();val x=m.groupValues[2].toInt();val y=m.groupValues[3].toInt()
        if(z !in 0..18||x !in 0 until (1 shl z)||y !in 0 until (1 shl z)||uri.query!=null)return response(400,"Bad request")
        if(System.currentTimeMillis()<blockedUntil)return response(503,"Backoff")
        var c:HttpURLConnection?=null
        try{
            c=URL("https://tile.openstreetmap.org/$z/$x/$y.png").openConnection() as HttpURLConnection
            c.connectTimeout=6000;c.readTimeout=6000;c.instanceFollowRedirects=false;c.useCaches=true
            c.setRequestProperty("User-Agent","DJ88-BID-Car-OS/1.0 (+https://github.com/Ionut061184/DJ88-BID-Car-OS)")
            c.setRequestProperty("Accept","image/png")
            val status=c.responseCode
            if(status==403||status==429){blockedUntil=System.currentTimeMillis()+600000;return response(503,"Provider limited")}
            if(status!=200||c.contentType?.substringBefore(";")!="image/png")return response(502,"Tile unavailable")
            val bytes=c.inputStream.use{input->
                val out=ByteArrayOutputStream();val buf=ByteArray(8192)
                while(true){val n=input.read(buf);if(n<0)break;if(out.size()+n>1000000)error("Tile too large");out.write(buf,0,n)}
                out.toByteArray()
            }
            if(!enabled||!foreground)return response(403,"Disabled")
            val headers=mutableMapOf<String,String>()
            for(name in listOf("Cache-Control","Expires","ETag","Last-Modified","Date","Age"))c.getHeaderField(name)?.let{headers[name]=it}
            if(!headers.containsKey("Cache-Control")&&!headers.containsKey("Expires"))headers["Cache-Control"]="max-age=604800"
            return WebResourceResponse("image/png",null,200,"OK",headers,ByteArrayInputStream(bytes))
        }catch(_:Exception){return response(503,"Tile unavailable")}
        finally{c?.disconnect()}
    }
}
