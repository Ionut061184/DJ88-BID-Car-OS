package ro.dj88bid.car

import android.app.Activity
import android.appwidget.AppWidgetHost
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProviderInfo
import android.content.ComponentName
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.FrameLayout
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.roundToInt

/** Separate host for user themes. Does not touch the existing MASTER map host. */
class BidThemeWidgets(private val activity:Activity,private val root:FrameLayout,private val web:WebView) {
    companion object { const val BIND=741; const val CONFIGURE=742 }
    private val host=AppWidgetHost(activity,8802)
    private val manager=AppWidgetManager.getInstance(activity)
    private val prefs=activity.getSharedPreferences("bid_theme_widget_bindings",Activity.MODE_PRIVATE)
    private val slots=mutableMapOf<String,FrameLayout>()
    private val widgetIds=mutableMapOf<String,Int>()
    private val sizes=mutableMapOf<String,String>()
    private var foreground=false
    private var pending=-1
    private var pendingKey=""
    private var pendingProvider=""
    private val trusted="file:///android_asset/index.html"
    private fun validKey(k:String)=k.matches(Regex("t[a-z0-9]{1,60}/e[a-z0-9]{1,60}"))
    private fun providerKey(p:AppWidgetProviderInfo)=p.provider.flattenToString()
    private fun providers()=manager.installedProviders.filter{it.profile==android.os.Process.myUserHandle()}
    init { 
        pending=prefs.getInt("_pending",-1)
        pendingKey=prefs.getString("_key","")?:""
        pendingProvider=prefs.getString("_provider","")?:""
    }
    private fun emit(k:String,ok:Boolean,message:String){
        if(web.url==trusted)web.evaluateJavascript("if(window.bidThemeWidgetResult)window.bidThemeWidgetResult("+JSONObject().put("key",k).put("ok",ok).put("message",message)+");",null)
    }
    @JavascriptInterface fun listProviders():String {
        val a=JSONArray()
        try{for(p in providers().sortedBy{it.loadLabel(activity.packageManager)})a.put(JSONObject().put("provider",providerKey(p)).put("label",p.loadLabel(activity.packageManager)).put("minWidth",p.minWidth).put("minHeight",p.minHeight))}catch(_:Exception){}
        return a.toString()
    }
    @JavascriptInterface fun binding(k:String,provider:String):Boolean {
        if(!validKey(k))return false
        return try{manager.getAppWidgetInfo(prefs.getInt(k,-1))?.let{providerKey(it)==provider}==true}catch(_:Exception){false}
    }
    @JavascriptInterface fun bind(k:String,provider:String) = activity.runOnUiThread {
        if(web.url!=trusted || !validKey(k) || pending>=0)return@runOnUiThread
        if(prefs.all.keys.count{validKey(it)}>=48 && !prefs.contains(k)){emit(k,false,"Limita de 48 autorizări locale.");return@runOnUiThread}
        val info=try{providers().firstOrNull{providerKey(it)==provider}}catch(_:Exception){null}
        if(info==null){emit(k,false,"Furnizorul nu mai este disponibil.");return@runOnUiThread}
        try{
            pending=host.allocateAppWidgetId();pendingKey=k;pendingProvider=provider
            if(!prefs.edit().putInt("_pending",pending).putString("_key",k).putString("_provider",provider).commit())error("Stocare indisponibilă")
            if(manager.bindAppWidgetIdIfAllowed(pending,info.profile,info.provider,null))configure()
            else activity.startActivityForResult(Intent(AppWidgetManager.ACTION_APPWIDGET_BIND)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,pending)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER,info.provider)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER_PROFILE,info.profile),BIND)
        }catch(e:Exception){fail("Autorizare eșuată: "+e.javaClass.simpleName)}
    }
    private fun configure(){
        try{
            val p=manager.getAppWidgetInfo(pending)
            if(p==null || providerKey(p)!=pendingProvider){fail("Asociere neconfirmată.");return}
            if(p.configure!=null)host.startAppWidgetConfigureActivityForResult(activity,pending,0,CONFIGURE,null)
            else finish()
        }catch(e:Exception){fail("Configurare eșuată: "+e.javaClass.simpleName)}
    }
    fun result(request:Int,code:Int):Boolean{
        if(request!=BIND && request!=CONFIGURE)return false
        if(pending<0)return true
        if(code!=Activity.RESULT_OK)fail("Autorizare sau configurare anulată.")
        else if(request==BIND)configure() else finish()
        return true
    }
    private fun finish(){
        val k=pendingKey
        if(!validKey(k)||manager.getAppWidgetInfo(pending)?.let{providerKey(it)}!=pendingProvider){fail("Furnizor neconfirmat.");return}
        val old=prefs.getInt(k,-1)
        if(!prefs.edit().putInt(k,pending).remove("_pending").remove("_key").remove("_provider").commit()){fail("Salvare nereușită.");return}
        pending=-1;pendingKey="";pendingProvider=""
        removeSlot(k)
        if(old>=0)try{host.deleteAppWidgetId(old)}catch(_:Exception){}
        emit(k,true,"Widget autorizat. Aplică tema pentru afișare.")
    }
    private fun fail(message:String){
        val k=pendingKey
        if(pending>=0)try{host.deleteAppWidgetId(pending)}catch(_:Exception){}
        pending=-1;pendingKey="";pendingProvider=""
        prefs.edit().remove("_pending").remove("_key").remove("_provider").apply()
        emit(k,false,message)
    }
    private fun removeSlot(k:String){slots.remove(k)?.let{root.removeView(it)};widgetIds.remove(k);sizes.remove(k)}
    @JavascriptInterface fun release(k:String)=activity.runOnUiThread{
        if(web.url!=trusted||!validKey(k))return@runOnUiThread
        val id=prefs.getInt(k,-1)
        if(prefs.edit().remove(k).commit()){removeSlot(k);if(id>=0)try{host.deleteAppWidgetId(id)}catch(_:Exception){};emit(k,false,"Autorizare eliminată.")}
    }
    fun start(){foreground=true;try{host.startListening()}catch(_:Exception){}}
    fun stop(){foreground=false;slots.values.forEach{it.visibility=View.GONE};try{host.stopListening()}catch(_:Exception){}}
    fun close(){stop();slots.keys.toList().forEach{removeSlot(it)}}
    @JavascriptInterface fun sync(raw:String)=activity.runOnUiThread{
        if(web.url!=trusted||!foreground||raw.length>24000){slots.values.forEach{it.visibility=View.GONE};return@runOnUiThread}
        val visible=mutableSetOf<String>()
        try{
            val data=JSONObject(raw);val vw=data.getDouble("vw");val vh=data.getDouble("vh")
            if(vw<=0||vh<=0||root.width<=0||root.height<=0)throw IllegalArgumentException()
            val list=data.getJSONArray("items")
            for(i in 0 until minOf(list.length(),16)){
                val e=list.getJSONObject(i);val k=e.getString("key");val provider=e.getString("provider")
                if(!validKey(k)||!binding(k,provider))continue
                val x=e.getDouble("x");val y=e.getDouble("y");val w=e.getDouble("w");val h=e.getDouble("h")
                if(!listOf(x,y,w,h).all{it.isFinite()}||x<0||y<0||w<1||h<1||x+w>vw+1||y+h>vh+1)continue
                val rect=intArrayOf((x*root.width/vw).roundToInt(),(y*root.height/vh).roundToInt(),(w*root.width/vw).roundToInt().coerceAtLeast(1),(h*root.height/vh).roundToInt().coerceAtLeast(1))
                val id=prefs.getInt(k,-1)
                val p=manager.getAppWidgetInfo(id)?:continue
                if(widgetIds[k]!=id)removeSlot(k)
                val slot=slots[k]?:FrameLayout(activity).apply{
                    setBackgroundColor(Color.TRANSPARENT);clipChildren=true
                    val v=host.createView(activity,id,p);v.setPadding(0,0,0,0);addView(v,FrameLayout.LayoutParams(-1,-1))
                    root.addView(this,FrameLayout.LayoutParams(1,1));slots[k]=this;widgetIds[k]=id
                }
                val signature=rect.joinToString(",")
                if(sizes[k]!=signature){
                    slot.layoutParams=FrameLayout.LayoutParams(rect[2],rect[3]).apply{leftMargin=rect[0];topMargin=rect[1]}
                    val density=activity.resources.displayMetrics.density
                    val requestedW=maxOf(rect[2],p.minWidth).coerceAtMost(4096)
                    val requestedH=maxOf(rect[3],p.minHeight).coerceAtMost(4096)
                    val v=slot.getChildAt(0)
                    val scale=minOf(rect[2].toFloat()/requestedW,rect[3].toFloat()/requestedH,1f)
                    v.layoutParams=FrameLayout.LayoutParams(requestedW,requestedH);v.pivotX=0f;v.pivotY=0f;v.scaleX=scale;v.scaleY=scale
                    v.translationX=(rect[2]-requestedW*scale)/2;v.translationY=(rect[3]-requestedH*scale)/2
                    val dw=(requestedW/density).roundToInt().coerceAtLeast(1);val dh=(requestedH/density).roundToInt().coerceAtLeast(1)
                    manager.updateAppWidgetOptions(id,Bundle().apply{putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH,dw);putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH,dw);putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,dh);putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT,dh)})
                    sizes[k]=signature
                }
                slot.alpha=e.optDouble("alpha",1.0).coerceIn(0.0,1.0).toFloat();slot.visibility=View.VISIBLE;visible.add(k)
            }
        }catch(_:Exception){}
        for(k in slots.keys.toList())if(k !in visible)removeSlot(k)
    }
}
