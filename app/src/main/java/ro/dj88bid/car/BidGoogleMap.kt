package ro.dj88bid.car

import android.app.Activity
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.FrameLayout
import com.google.android.gms.common.GoogleApiAvailability
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.GoogleMapOptions
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.MapStyleOptions
import org.json.JSONObject
import kotlin.math.roundToInt

/** Official SDK, one visible map per page. No key from any third-party APK. */
class BidGoogleMap(private val activity:Activity,private val root:FrameLayout,private val web:WebView) {
    private val trusted="file:///android_asset/index.html"
    private val slot=FrameLayout(activity).apply{visibility=View.GONE;setBackgroundColor(Color.BLACK)}
    private var view:MapView?=null
    private var map:GoogleMap?=null
    private var foreground=false
    private var started=false
    private var loaded=false
    private var previous=""
    private var lastCamera=""
    private var detail="Neinițializat"
    private var settings=""
    init{root.addView(slot,FrameLayout.LayoutParams(1,1))}
    private fun hasKey():Boolean=try {
        val key=activity.packageManager.getApplicationInfo(activity.packageName,PackageManager.GET_META_DATA)
            .metaData?.getString("com.google.android.geo.API_KEY").orEmpty()
        key.isNotBlank() && key!="BID_KEY_NOT_CONFIGURED"
    }catch(_:Exception){false}
    private fun services()=try{GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(activity)}catch(_:Exception){-1}
    @JavascriptInterface fun status():String=JSONObject().put("keyConfigured",hasKey()).put("playServices",services())
        .put("sdkReady",map!=null).put("tilesLoaded",loaded).put("detail",detail).toString()
    private fun emit(){if(web.url==trusted)web.evaluateJavascript("if(window.bidGoogleMapState)window.bidGoogleMapState("+status()+");",null)}
    fun start(){foreground=true;emit()}
    fun stop(){foreground=false;hide()}
    fun lowMemory(){view?.onLowMemory()}
    fun close(){hide();try{view?.onDestroy()}catch(_:Exception){};view=null;map=null;root.removeView(slot)}
    private fun hide(){
        slot.visibility=View.GONE
        if(started){try{view?.onPause();view?.onStop()}catch(_:Exception){};started=false}
        previous="";lastCamera="";settings=""
    }
    private fun ensure():Boolean{
        if(!hasKey()){detail="Cheia Google Maps BID nu este configurată.";return false}
        if(services()!=0){detail="Google Play Services indisponibil: "+services();return false}
        if(view!=null)return true
        try{
            val v=MapView(activity,GoogleMapOptions().mapType(GoogleMap.MAP_TYPE_NORMAL).compassEnabled(true).zoomControlsEnabled(false))
            view=v;slot.addView(v,FrameLayout.LayoutParams(-1,-1));v.onCreate(Bundle())
            v.getMapAsync{g->
                map=g;detail="SDK inițializat; încărcarea hărții trebuie confirmată."
                g.uiSettings.isMapToolbarEnabled=false
                g.setOnMapLoadedCallback{loaded=true;detail="SDK a raportat încărcarea hărții; verifică vizual.";emit()}
                emit()
            }
            return true
        }catch(e:Exception){detail="Inițializare: "+e.javaClass.simpleName;try{view?.onDestroy()}catch(_:Exception){};view=null;map=null;slot.removeAllViews();return false}
    }
    @JavascriptInterface fun sync(raw:String)=activity.runOnUiThread{
        if(web.url!=trusted||!foreground||raw.length>4000){hide();return@runOnUiThread}
        try{
            val j=JSONObject(raw)
            if(!j.optBoolean("show")){hide();return@runOnUiThread}
            val vw=j.getDouble("vw");val vh=j.getDouble("vh");val x=j.getDouble("x");val y=j.getDouble("y");val w=j.getDouble("w");val h=j.getDouble("h")
            val lat=j.getDouble("lat");val lon=j.getDouble("lon")
            if(!listOf(vw,vh,x,y,w,h,lat,lon).all{it.isFinite()}||vw<=0||vh<=0||w<100||h<80||x<0||y<0||x+w>vw+1||y+h>vh+1||lat !in -85.0..85.0||lon !in -180.0..180.0){hide();return@runOnUiThread}
            if(!ensure()){hide();emit();return@runOnUiThread}
            if(root.width<=0||root.height<=0){hide();return@runOnUiThread}
            val rect=listOf((x*root.width/vw).roundToInt(),(y*root.height/vh).roundToInt(),(w*root.width/vw).roundToInt(),(h*root.height/vh).roundToInt())
            val sig=rect.joinToString(",")
            if(sig!=previous){slot.layoutParams=FrameLayout.LayoutParams(rect[2],rect[3]).apply{leftMargin=rect[0];topMargin=rect[1]};previous=sig}
            slot.alpha=j.optDouble("alpha",1.0).coerceIn(0.35,1.0).toFloat()
            slot.visibility=View.VISIBLE
            if(!started){view?.onStart();view?.onResume();started=true}
            val g=map?:return@runOnUiThread
            val mode=j.optString("mode","normal")
            val stationary=j.optBoolean("stationary")
            val config=mode+":"+j.optBoolean("traffic")+":"+stationary
            if(settings!=config){
                g.mapType=when(mode){"satellite"->GoogleMap.MAP_TYPE_SATELLITE;"hybrid"->GoogleMap.MAP_TYPE_HYBRID;"terrain"->GoogleMap.MAP_TYPE_TERRAIN;else->GoogleMap.MAP_TYPE_NORMAL}
                g.setMapStyle(if(mode=="night")MapStyleOptions("[{\"elementType\":\"geometry\",\"stylers\":[{\"color\":\"#24202a\"}]},{\"elementType\":\"labels.text.fill\",\"stylers\":[{\"color\":\"#dac6ad\"}]}]") else null)
                g.isTrafficEnabled=j.optBoolean("traffic")
                g.uiSettings.setAllGesturesEnabled(stationary);settings=config
            }
            val zoom=j.optDouble("zoom",16.0).coerceIn(3.0,20.0).toFloat()
            val bearing=j.optDouble("bearing",0.0).let{if(it.isFinite())((it%360+360)%360).toFloat() else 0f}
            val camera="$lat,$lon,$zoom,$bearing"
            if(camera!=lastCamera){g.moveCamera(CameraUpdateFactory.newCameraPosition(CameraPosition(LatLng(lat,lon),zoom,0f,bearing)));lastCamera=camera}
        }catch(e:Exception){detail="Hartă indisponibilă: "+e.javaClass.simpleName;hide();emit()}
    }
}
