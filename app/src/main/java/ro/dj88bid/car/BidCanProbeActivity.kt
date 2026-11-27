package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.content.*
import android.content.pm.PackageManager
import android.os.*
import android.graphics.Color
import android.widget.*
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.Locale

/** Isolated diagnostic. Only OEM service discovery, normal bind, two read-only subscriptions
 * and their removal. No SDK credentials, initialization, CAN writes, query commands or network. */
class BidCanProbeActivity : Activity() {
    companion object {
        const val PKG = "com.qf.vehicle"
        const val SERVICE = "com.qf.vehicle.service.VehicleService"
        const val ACTION = "com.qf.vehicle.service.ACTION_CAN_SERVICE"
        const val FEATURE = "com.qf.vehicle.service.ICanBusServiceFeature"
        const val CALLBACK = "com.qf.vehicle.service.ICanBusServiceCallback"
        const val VERSION = "V1.11-260615.1900"
        const val SHA = "b99f3c6f139f6a33b5c7ca3a70cc536246b852a8ec53ac0cee9732ff2ae6dc74"
        const val BODY_ADD = 11
        const val BODY_REMOVE = 12
        const val DOOR_ADD = 5
        const val DOOR_REMOVE = 6
        const val PACKED = 2
    }
    private val ui = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor { r -> Thread(r,"bid-can-probe").apply { isDaemon=true } }
    private lateinit var report: TextView
    private lateinit var start: Button
    private lateinit var stop: Button
    private val notes = mutableListOf<String>()
    private var deadline = 0L
    private var epoch = 0
    private var running = false
    private var bound = false
    private var connection: ServiceConnection? = null
    private var remote: IBinder? = null
    private var current: Session? = null
    private var bodyCount = 0L
    private var doorCount = 0L
    private var lastBody = 0L
    private var lastDoor = 0L
    private var bodySize = 0
    private var doorSize = 0
    private var version = "—"
    private var hash = "—"
    private var descriptor = "—"
    private var stage = "Neînceput"
    private var uid = -1
    private var phase = "OEM: stare neconfirmată"
    private val samples = ArrayDeque<String>()

    private class Session(val binder: IBinder,val body: IBinder,val door: IBinder) {
        @Volatile var bodyAttempt = false
        @Volatile var doorAttempt = false
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL; setPadding(16,12,16,12)
            setBackgroundColor(0xff210f17.toInt())
        }
        root.addView(TextView(this).apply { text="DJ 88 BID · QF001 CANBUS DIAGNOSTIC"; textSize=21f; setTextColor(0xffe6c79a.toInt()) })
        root.addView(TextView(this).apply {
            text="Numai recepție. Testează cu mașina parcată. Nicio comandă către CAN sau MCU."; textSize=13f; setTextColor(Color.WHITE)
        })
        val controls=LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL }
        fun button(label:String, action:()->Unit):Button = Button(this).apply {
            text=label; isAllCaps=false; textSize=13f; setOnClickListener{action()}
            controls.addView(this,LinearLayout.LayoutParams(0,-2,1f))
        }
        start=button("Pornește testul"){confirm()}
        stop=button("Oprește"){finishSession("Oprit manual")}
        button("Deschide OEM"){openOem()}
        button("Marchează etapa"){mark()}
        button("Copiază raport"){copyReport()}
        root.addView(controls)
        report=TextView(this).apply { setTextColor(Color.WHITE);textSize=14f;setTextIsSelectable(true) }
        root.addView(ScrollView(this).apply { addView(report) },LinearLayout.LayoutParams(-1,0,1f))
        setContentView(root); render()
    }

    private fun confirm(){
        if(running)return
        AlertDialog.Builder(this).setTitle("Test de recepție QF001")
            .setMessage("Confirmă că mașina este parcată. Testul durează cel mult 120 s și se poate continua când deschizi aplicația OEM. Nu trimite comenzi CAN, nu cere root, nu folosește acreditări OEM.")
            .setPositiveButton("Mașina este parcată"){_,_->begin()}
            .setNegativeButton("Renunță",null).show()
    }
    private fun note(msg:String){
        if(notes.size>=30)notes.removeAt(0)
        notes.add(msg)
    }
    private fun begin(){
        if(running)return
        val token=++epoch
        running=true; deadline=SystemClock.elapsedRealtime()+120000
        notes.clear();samples.clear();bodyCount=0;doorCount=0;lastBody=0;lastDoor=0
        bodySize=0;doorSize=0;version="—";hash="—";descriptor="—";stage="Verificare APK OEM";phase="OEM: stare neconfirmată"
        render();ui.post(tick)
        worker.execute {
            try {
                val p=packageManager.getPackageInfo(PKG,0)
                val component=ComponentName(PKG,SERVICE)
                val info=packageManager.getServiceInfo(component,PackageManager.MATCH_DISABLED_COMPONENTS)
                val app=p.applicationInfo ?: error("Aplicație OEM fără informații")
                val digest=MessageDigest.getInstance("SHA-256")
                File(app.sourceDir).inputStream().use { input ->
                    val b=ByteArray(65536)
                    while(true){val n=input.read(b);if(n<0)break;digest.update(b,0,n)}
                }
                val sum=digest.digest().joinToString(""){String.format(Locale.ROOT,"%02x",it.toInt() and 255)}
                ui.post {
                    if(!running||token!=epoch)return@post
                    version=p.versionName?:"—";hash=sum;uid=app.uid
                    note("Serviciu exportat: ${info.exported}; activ: ${info.enabled && app.enabled}; permisiune: ${info.permission?:"niciuna declarată"}")
                    if(version!=VERSION || sum!=SHA){finishSession("Versiune / SHA diferit. Oprit înainte de bind; trebuie verificat APK-ul instalat.");return@post}
                    if(!info.exported || !info.enabled || !app.enabled){finishSession("Serviciu indisponibil");return@post}
                    val permission=info.permission
                    if(!permission.isNullOrEmpty() && checkSelfPermission(permission)!=PackageManager.PERMISSION_GRANTED){
                        finishSession("Permisiune OEM refuzată: $permission");return@post
                    }
                    bind(token)
                }
            } catch(e:Exception) {
                ui.post { if(running&&token==epoch)finishSession("Inspecție OEM: "+e.javaClass.simpleName) }
            }
        }
    }

    private fun bind(token:Int){
        stage="Conectare la serviciul original"
        val conn=object:ServiceConnection{
            override fun onServiceConnected(name:ComponentName,binder:IBinder){
                if(!running||token!=epoch)return
                remote=binder;stage="Verificare descriptor Binder";render()
                worker.execute {
                    try {
                        val desc=binder.interfaceDescriptor
                        ui.post {
                            if(!running||token!=epoch)return@post
                            descriptor=desc?:"—"
                            if(desc!=FEATURE){finishSession("Descriptor neașteptat. Nicio tranzacție.");return@post}
                            subscribe(token,binder)
                        }
                    }catch(e:Exception){ui.post{if(running&&token==epoch)finishSession("Descriptor refuzat: "+e.javaClass.simpleName)}}
                }
            }
            override fun onServiceDisconnected(name:ComponentName){if(running&&token==epoch)finishSession("Serviciul OEM s-a deconectat")}
            override fun onNullBinding(name:ComponentName){if(running&&token==epoch)finishSession("Serviciul OEM a returnat null")}
            override fun onBindingDied(name:ComponentName){if(running&&token==epoch)finishSession("Legătura OEM a expirat")}
        }
        connection=conn
        try{
            bound=bindService(Intent(ACTION).setComponent(ComponentName(PKG,SERVICE)),conn,Context.BIND_AUTO_CREATE)
            if(!bound){finishSession("Android a refuzat bindService");return}
            note("bindService acceptat. Se așteaptă Binder.")
            ui.postDelayed({if(running&&token==epoch&&remote==null)finishSession("Timeout: Binder nu a fost livrat")},15000)
        }catch(e:Exception){finishSession("bindService: "+e.javaClass.simpleName)}
        render()
    }

    private fun callback(token:Int, isBody:Boolean,expectedUid:Int):Binder = object:Binder(){
        init{attachInterface(null,CALLBACK)}
        override fun onTransact(code:Int,data:Parcel,reply:Parcel?,flags:Int):Boolean{
            if(code==INTERFACE_TRANSACTION){reply?.writeString(CALLBACK);return true}
            if(code!=PACKED)return super.onTransact(code,data,reply,flags)
            if(Binder.getCallingUid()!=expectedUid)throw SecurityException("Unexpected sender UID")
            data.enforceInterface(CALLBACK)
            if(data.dataAvail()>8192)throw IllegalArgumentException("Oversized parcel")
            val bytes=data.createByteArray()
            if(bytes!=null&&bytes.size<=4096){
                val size=bytes.size
                val prefix=bytes.take(64).joinToString(" "){String.format(Locale.ROOT,"%02X",it.toInt() and 255)}
                val at=SystemClock.elapsedRealtime()
                ui.post {
                    if(running&&token==epoch){
                        if(isBody){bodyCount++;lastBody=at;bodySize=size}else{doorCount++;lastDoor=at;doorSize=size}
                        val item=(if(isBody)"CARBODY" else "DOOR")+" · "+size+" B · "+prefix
                        if(samples.lastOrNull()!=item){
                            if(samples.size>=6)samples.removeFirst()
                            samples.addLast(item)
                        }
                    }
                }
            }
            reply?.writeNoException()
            return true
        }
    }
    // Only the four transaction numbers independently verified in V1.11 DEX.
    private fun subscription(binder:IBinder,code:Int,cb:IBinder){
        require(code in setOf(BODY_ADD,BODY_REMOVE,DOOR_ADD,DOOR_REMOVE))
        val data=Parcel.obtain();val reply=Parcel.obtain()
        try{
            data.writeInterfaceToken(FEATURE);data.writeStrongBinder(cb)
            if(!binder.transact(code,data,reply,0))error("Transaction not accepted")
            reply.readException()
        }finally{data.recycle();reply.recycle()}
    }
    private fun subscribe(token:Int,binder:IBinder){
        val session=Session(binder,callback(token,true,uid),callback(token,false,uid))
        current=session;stage="Înregistrare caroserie / uși";render()
        worker.execute {
            val outcomes=mutableListOf<String>()
            try{session.bodyAttempt=true;subscription(binder,BODY_ADD,session.body);outcomes.add("CARBODY: apel acceptat (void; recepția încă neconfirmată)")}
            catch(e:Exception){outcomes.add("CARBODY: "+e.javaClass.simpleName)}
            try{session.doorAttempt=true;subscription(binder,DOOR_ADD,session.door);outcomes.add("DOOR: apel acceptat (void; recepția încă neconfirmată)")}
            catch(e:Exception){outcomes.add("DOOR: "+e.javaClass.simpleName)}
            ui.post{
                if(running&&token==epoch){outcomes.forEach{note(it)};stage="Ascultare pasivă · fără inițializare SDK OEM";render()}
            }
        }
    }

    private fun finishSession(reason:String){
        if(!running)return
        running=false;++epoch;stage=reason;note(reason);ui.removeCallbacks(tick)
        val session=current;current=null;remote=null
        val conn=connection;connection=null
        val wasBound=bound;bound=false
        if(session!=null){
            worker.execute{
                // Cleanup only subscriptions previously attempted.
                val results=mutableListOf<String>()
                if(session.bodyAttempt)try{subscription(session.binder,BODY_REMOVE,session.body);results.add("CARBODY: dezabonare acceptată")}catch(_:Exception){results.add("CARBODY: dezabonare neconfirmată")}
                if(session.doorAttempt)try{subscription(session.binder,DOOR_REMOVE,session.door);results.add("DOOR: dezabonare acceptată")}catch(_:Exception){results.add("DOOR: dezabonare neconfirmată")}
                ui.post { if(!isDestroyed){results.forEach{note(it)};render()} }
            }
        }
        if(wasBound&&conn!=null)try{unbindService(conn)}catch(_:Exception){}
        render()
    }
    private val tick=object:Runnable{
        override fun run(){
            if(!running)return
            if(SystemClock.elapsedRealtime()>=deadline){finishSession("Test terminat (120 s)");return}
            render();ui.postDelayed(this,1000)
        }
    }
    private fun openOem(){
        try{
            val i=packageManager.getLaunchIntentForPackage(PKG)
            if(i==null){note("OEM fără activitate de lansare vizibilă; deschide manual Informații vehicul.");render()}
            else{note("Deschidere OEM solicitată; marchează manual ecranul deschis.");render();startActivity(i)}
        }catch(e:Exception){note("OEM: "+e.javaClass.simpleName);render()}
    }
    private fun mark(){
        AlertDialog.Builder(this).setTitle("Marchează starea testului")
            .setItems(arrayOf("OEM închis","Informații despre caroserie deschise","Informații despre vehicul deschise")){_,i->
                phase=listOf("OEM închis","Caroserie deschisă","Vehicul deschis")[i]
                note("$phase · CARBODY=$bodyCount DOOR=$doorCount");render()
            }.show()
    }
    private fun summary():String{
        val now=SystemClock.elapsedRealtime()
        fun age(last:Long)=if(last==0L)"—" else ((now-last)/1000).toString()+" s"
        return buildString{
            appendLine("Stadiu: $stage")
            if(running)appendLine("Timp rămas: "+((deadline-now).coerceAtLeast(0)/1000)+" s")
            appendLine("OEM: $version");appendLine("SHA-256: $hash");appendLine("Binder: $descriptor")
            appendLine("CARBODY: $bodyCount mesaje · ultimul $bodySize B · vârstă ${age(lastBody)}")
            appendLine("DOOR: $doorCount mesaje · ultimul $doorSize B · vârstă ${age(lastDoor)}")
            appendLine("Etapă: $phase")
            appendLine("Nicio valoare interpretată sau simulată. Nicio inițializare cu acreditări OEM.")
            appendLine();notes.forEach{appendLine(it)}
            if(samples.isNotEmpty()){appendLine();appendLine("Eșantioane locale (max. 64 B fiecare):");samples.forEach{appendLine(it)}}
        }
    }
    private fun render(){
        if(!::report.isInitialized)return
        report.text=summary();start.isEnabled=!running;stop.isEnabled=running
    }
    private fun copyReport(){
        val clipboard=getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("BID CAN diagnostic",summary()))
        Toast.makeText(this,"Raport copiat local",Toast.LENGTH_SHORT).show()
    }
    override fun onDestroy(){
        finishSession("Activitate închisă");ui.removeCallbacksAndMessages(null);worker.shutdown();super.onDestroy()
    }
}
