package ro.dj88bid.car

import android.app.Activity
import android.app.WallpaperManager
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.ColorDrawable
import android.view.WindowManager
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject

/** Reuse the system-selected wallpaper. Never set or replace it programmatically. */
class BidSystemWallpaper(private val activity:Activity,private val web:WebView) {
    private val trusted="file:///android_asset/index.html"
    private val initialBackground=activity.window.decorView.background
    private val initialFormat=activity.window.attributes.format
    private var foreground=false
    private var shown=false
    private fun supported():Boolean=try {
        WallpaperManager.getInstance(activity).isWallpaperSupported
    }catch(_:Exception){false}
    @JavascriptInterface fun capabilities():String=JSONObject()
        .put("supported",supported())
        .put("live",activity.packageManager.hasSystemFeature("android.software.live_wallpaper"))
        .toString()
    private fun emit(ok:Boolean,message:String){
        if(web.url==trusted)web.evaluateJavascript("if(window.bidSystemWallpaperResult)window.bidSystemWallpaperResult("+JSONObject().put("requested",ok).put("message",message)+");",null)
    }
    private fun hide(){
        if(!shown)return
        activity.window.clearFlags(WindowManager.LayoutParams.FLAG_SHOW_WALLPAPER)
        activity.window.setBackgroundDrawable(initialBackground ?: ColorDrawable(Color.BLACK))
        activity.window.setFormat(initialFormat)
        web.setBackgroundColor(Color.BLACK)
        shown=false
    }
    fun start(){foreground=true;if(web.url==trusted)web.evaluateJavascript("if(window.bidSystemWallpaperRefresh)window.bidSystemWallpaperRefresh();",null)}
    fun stop(){foreground=false;hide();emit(false,"Fundal suspendat.")}
    @JavascriptInterface fun show(wanted:Boolean)=activity.runOnUiThread{
        if(web.url!=trusted||!foreground||!wanted||!supported()){
            hide();emit(false,if(wanted)"Fundalul de sistem este indisponibil." else "Fundal BID activ.");return@runOnUiThread
        }
        try{
            if(!shown){
                activity.window.setFormat(PixelFormat.TRANSLUCENT)
                activity.window.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
                web.setBackgroundColor(Color.TRANSPARENT)
                activity.window.addFlags(WindowManager.LayoutParams.FLAG_SHOW_WALLPAPER)
                shown=true
            }
            emit(true,"Afișare solicitată sistemului Android; verifică vizual.")
        }catch(_:Exception){hide();emit(false,"Android nu a acceptat fundalul de sistem.")}
    }
    @JavascriptInterface fun choose()=activity.runOnUiThread{
        if(web.url!=trusted||!foreground)return@runOnUiThread
        if(!activity.packageManager.hasSystemFeature("android.software.live_wallpaper")){
            emit(false,"Dispozitivul nu declară suport pentru fundaluri live.");return@runOnUiThread
        }
        try{activity.startActivity(Intent(WallpaperManager.ACTION_LIVE_WALLPAPER_CHOOSER))}
        catch(_:Exception){emit(false,"Selectorul Android de fundaluri live lipsește.")}
    }
}
