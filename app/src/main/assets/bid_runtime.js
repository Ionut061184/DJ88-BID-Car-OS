function fit(){const el=document.getElementById('stage');const s=Math.min(innerWidth/1280,innerHeight/720);el.style.transform='scale('+s+')';el.style.left=((innerWidth-1280*s)/2)+'px';el.style.top=((innerHeight-720*s)/2)+'px'}addEventListener('resize',fit);fit();
function tick(){
 const d=new Date();
 document.getElementById('clock').textContent=d.toLocaleTimeString('ro-RO',{hour:'2-digit',minute:'2-digit'});
 // Fixed compact format fits the limited QF001 top status slot at 1280x720.
 const dateText=d.toLocaleDateString('ro-RO',{day:'2-digit',month:'2-digit',year:'numeric'});
 document.getElementById('dateLive').textContent=dateText;
 const hour=d.getHours(); const night=hour>=20||hour<7;
 document.getElementById('nightTint').style.opacity=night?'0.18':'0';
}
tick();setInterval(tick,10000);
/* Read only the battery reported by Android, when supported by this head unit.
   The CANBUS vehicle-voltage slot never shows a fabricated number. */
function refreshAndroidBattery(){
 const out=document.getElementById('batteryAndroidLive');
 if(!out)return;
 let pct=null;
 try{
  if(window.BID&&typeof BID.batterySnapshot==='function'){
   const d=JSON.parse(BID.batterySnapshot());
   if(Number.isInteger(d.percent)&&d.percent>=0&&d.percent<=100)pct=d.percent;
  }
 }catch(e){pct=null;}
 out.textContent=pct===null?'🔋 —':'🔋 '+pct+'%';
 out.title=pct===null?'Baterie Android: senzor indisponibil':'Baterie Android: '+pct+'%';
 const car=document.getElementById('voltageLive');
 if(car){
  let realVolts=null;
  try {
   if(window.BID&&typeof BID.vehicleVoltageSnapshot==='function'){
    const v=JSON.parse(BID.vehicleVoltageSnapshot());
    if(v.available===true&&typeof v.volts==='number'&&
       Number.isFinite(v.volts)&&v.volts>=9&&v.volts<=16.5) realVolts=v.volts;
   }
  }catch(e){realVolts=null}
  car.textContent=realVolts===null?'— V':realVolts.toFixed(1)+' V';
  car.title=realVolts===null?
   'Tensiune auto: QF001 nu permite citirea sau nu furnizează date':
   'Tensiune auto citită din QF001 · '+realVolts.toFixed(1)+' V';
 }
}
refreshAndroidBattery();setInterval(refreshAndroidBattery,10000);

function statusNotice(msg){const el=document.getElementById('statusNotice');el.textContent=msg;el.style.display='block';clearTimeout(window.bidNoticeTimer);window.bidNoticeTimer=setTimeout(()=>el.style.display='none',3800)}
function canUnsupported(name){statusNotice(name+': date CANBUS încă neverificate; comanda OEM nu este simulată.')}
function mediaKey(action){if(window.BID && typeof BID.mediaKey==='function'){BID.mediaKey(action)}else statusNotice('Comanda media nu este disponibilă în browser.')}
function goHome(){
 closeAll();
 try{window.scrollTo(0,0)}catch(e){}
 statusNotice('BID Luxury · Acasă');
}
function batteryDetails(){
 let voltage=document.getElementById('voltageLive');
 let android=document.getElementById('batteryAndroidLive');
 const v=voltage?voltage.textContent.trim():'— V';
 const a=android?android.textContent.trim():'—';
 statusNotice('Baterie Android: '+a+' · Baterie auto QF001: '+v);
}
function configureWeather(){if(window.BID && typeof BID.chooseWeatherCity==='function'){BID.chooseWeatherCity()}else statusNotice('Vremea live necesită conexiune și aplicația Android.')}
function updateWeather(city,temperature,description){let el=document.getElementById('weatherLive');el.textContent=temperature===null?'Vreme indisponibilă · '+city:description+' '+temperature+'°C · '+city;}
function updateMedia(title,playing){const el=document.getElementById('mediaLive');el.textContent=title||'Media: fără date';}
function openMusicMenu(){
 closeAll();
 // Match the native 5x2 Apps drawer: large OEM icons and swipeable pages.
 if(window.BID && typeof BID.showFunctionsGrid==='function'){
  BID.showFunctionsGrid();
  return;
 }
 // Browser-only preview fallback (no native Android integration).
 document.getElementById('musicMenu').classList.add('on');
}
function closeMusicMenu(){document.getElementById('musicMenu').classList.remove('on')}
function musicChoose(kind){
 closeMusicMenu();
 if(kind==='youtube'){launch('youtube');return}
 if(kind==='maps'){launch('maps');return}
 if(kind==='car'||kind==='canbus'){launch(kind);return}
 if(kind==='reverse'){statusNotice('Camera marșarier funcționează automat la selectarea treptei R, prin sistemul original QF001.');return}
 if(kind==='oem'){oemFunctions();return}
 if(window.BID && typeof BID.openMediaOem==='function'){BID.openMediaOem(kind)}
 else statusNotice('Funcția multimedia necesită aplicația pe navigație.');
}
function luxury(on=true){
 document.getElementById('luxuryModal').classList.toggle('on',on);
 if(on){theme(false);document.getElementById('drive').classList.remove('on');document.getElementById('diagnosticModal').classList.remove('on');localStorage.setItem('bid_mode','luxury')}
}
function luxuryLaunch(cmd){luxury(false);launch(cmd)}
function luxuryAuto(action){luxury(false);autoLaunch(action)}
function theme(on){document.getElementById('overlay').classList.toggle('on',on)}
function closeAll(){closeMusicMenu();luxury(false);document.getElementById('diagnosticModal').classList.remove('on');theme(false);document.getElementById('drive').classList.remove('on');localStorage.setItem('bid_mode','luxury')}
function driving(){luxury(false);theme(false);document.getElementById('drive').classList.add('on');localStorage.setItem('bid_mode','driving')}
function launch(cmd){if(window.BID&&typeof BID.open==='function'){BID.open(cmd);return}alert('Comanda '+cmd+' necesită aplicația Android.')}
function autoConfig(action){if(window.BID&&typeof BID.configureAuto==='function')BID.configureAuto(action);else alert('Disponibil doar în aplicația Android.')}
function autoLaunch(action){if(window.BID&&typeof BID.launchAuto==='function')BID.launchAuto(action);else alert('Disponibil doar în aplicația Android.')}
function oemFunctions(){if(window.BID&&typeof BID.showOemFunctions==='function')BID.showOemFunctions();else statusNotice('Funcțiile originale necesită navigația QF001.');}
function qfThemes(){if(window.BID&&typeof BID.openQfThemes==='function')BID.openQfThemes();else alert('Selectorul Themes QF001 este disponibil doar pe navigatia originala.')} 
function autoApps(){
 if(window.BID && typeof BID.showCarApps==='function') BID.showCarApps();
 else alert('Disponibil doar în aplicația Android.');
}
function diagnostic(){
 let msg='Testarea pe QF001 nu a fost realizată.';
 try {
  if(window.BID){
   const d=JSON.parse(BID.diagnostics());
   const homes=Array.isArray(d.availableHomeLaunchers)?d.availableHomeLaunchers:[];
   const car=Array.isArray(d.candidateCarApps)?d.candidateCarApps:[];
   const assigned=d.assignedAutoShortcuts||{};const bindings=Object.keys(assigned).map(k=>assigned[k].label+': '+assigned[k].package+(assigned[k].available?' (disponibil)':' (neconfigurat / indisponibil)')).join(', ');
   const canbusComponents=Array.isArray(d.canbusExportedComponents)?d.canbusExportedComponents:[];
   const canbusEntries=canbusComponents.map(c=>c.type+': '+c.name+(c.permission?' [permisiune: '+c.permission+']':'')).join('\\n');
   const oem=d.originalQf001Apps||{};const oemSummary=Object.keys(oem).map(k=>k+': '+oem[k].package+(oem[k].launchableVisible?' (detectat)':' (absent / invizibil)')).join(', ');
   msg='CANBUS OEM: '+(d.canbusPackageVisible?'pachet vizibil':'pachet absent/invizibil')+
   '; lansabil: '+(d.canbusHasPublicLauncher?'DA':'NU')+
   '; date climatizare/tensiune: NECONECTATE\\n'+
   'Dispozitiv: '+(d.deviceManufacturer||'?')+' '+(d.deviceModel||'?')+
   '\nAndroid: '+(d.androidRelease||'?')+
   '\nSwoodGrain vizibil: '+(d.originalSwoodGrainVisible?'DA':'NU / necunoscut')+
   '\nLaunchere HOME detectate: '+homes.map(x=>x.label+' ['+x.package+']').join(', ')+
   '\nMaps: '+d.mapsInstalled+'; Waze: '+d.wazeInstalled+'; YouTube: '+d.youtubeInstalled+
   '\nComponente CANBUS exportate (inventar): '+(canbusEntries||'niciuna vizibilă')+'\nScurtături auto: '+bindings+'\nAplicații OEM QF001 din firmware: '+oemSummary+'\nRadio/DSP/BT auto QF001: NETESTATE. Nu se modifică Themes original.';
  }
 } catch(e) { msg='Diagnostic indisponibil.'; }
 document.getElementById('diagnosticText').textContent=msg.replace(/\\n/g, '\n');
 theme(false);
 document.getElementById('diagnosticModal').classList.add('on');
}
try{if(localStorage.getItem('bid_mode')==='driving')driving()}catch(e){}


/* Native Maps preview: separate from the immutable Luxury screen. */
(function(){
 const drive=document.getElementById('drive'), panel=document.querySelector('#overlay .row');
 if(!drive||!panel)return;
 const key='bid_native_maps_driving_v1';
 const defaults={mode:'normal',zoom:16,traffic:false,heading:false,x:0,y:0,w:100,h:100,alpha:1,border:'#b49a7e',borderWidth:3};
 let prefs={...defaults},fix=null,fixAt=0,active=false,editing=false;
 try{prefs={...defaults,...JSON.parse(localStorage.getItem(key)||'{}')}}catch(e){}
 const modes=['normal','satellite','hybrid','terrain','night'];
 if(!modes.includes(prefs.mode))prefs.mode='normal';
 prefs.zoom=Math.min(20,Math.max(3,Number(prefs.zoom)||16));
 const entry=document.createElement('button');entry.textContent='Google Maps nativ · Test';panel.appendChild(entry);
 const box=document.createElement('section');
 box.style.cssText='display:none;position:absolute;inset:70px 20px 20px;background:#211b20;color:#e6d2bc;padding:12px;z-index:5;box-sizing:border-box';
 box.innerHTML='<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap"><button data-close>Înapoi</button><label>Hartă <select data-mode><option value="normal">Normală</option><option value="satellite">Satelit</option><option value="hybrid">Hibrid</option><option value="terrain">Relief</option><option value="night">Noapte</option></select></label><label>Zoom <input data-zoom type="range" min="3" max="20" step="1"></label><label><input data-traffic type="checkbox"> Trafic</label><label><input data-heading type="checkbox"> Direcție GPS</label></div><p data-status role="status">Aștept GPS.</p><div data-map style="position:absolute;top:125px;left:12px;right:12px;bottom:12px;background:#151515;display:grid;place-items:center">Hartă nativă · necesită GPS și cheia BID</div>';
 drive.appendChild(box);
 const q=s=>box.querySelector(s),mode=q('[data-mode]'),zoom=q('[data-zoom]'),traffic=q('[data-traffic]'),heading=q('[data-heading]'),slot=q('[data-map]'),status=q('[data-status]');
 mode.value=prefs.mode;zoom.value=prefs.zoom;traffic.checked=!!prefs.traffic;heading.checked=!!prefs.heading;
 const area=document.createElement('div');
 area.style.cssText='position:absolute;top:190px;left:12px;right:12px;bottom:12px;overflow:hidden;border:1px solid #62564d;box-sizing:border-box';
 box.insertBefore(area,slot);area.appendChild(slot);
 const controls=document.createElement('div');
 controls.style.cssText='display:flex;gap:8px;align-items:center;flex-wrap:wrap';
 q('[data-status]').before(controls);
 const clamp=(n,min,max,fallback)=>Number.isFinite(Number(n))?Math.min(max,Math.max(min,Number(n))):fallback;
 const fields={};
 for(const [k,label,min] of [['x','X',0],['y','Y',0],['w','Lățime',30],['h','Înălțime',30]]){
  const l=document.createElement('label'),i=document.createElement('input');
  i.type='number';i.min=min;i.max=100;i.step=5;i.style.width='54px';l.textContent=label+' % ';l.appendChild(i);controls.appendChild(l);fields[k]=i;
  i.addEventListener('change',()=>{prefs[k]=clamp(i.value,min,100,defaults[k]);applyLayout(k);save()});
 }
 const edit=document.createElement('button');edit.textContent='Editează tactil';controls.appendChild(edit);
 const styleControls=document.createElement('div');styleControls.style.cssText='display:flex;gap:12px;align-items:center;flex-wrap:wrap';controls.after(styleControls);
 function styleField(label,type,min,max,step,value,handler){
  const l=document.createElement('label'),i=document.createElement('input');l.textContent=label+' ';i.type=type;if(min!==null){i.min=min;i.max=max;i.step=step}i.value=value;l.appendChild(i);styleControls.appendChild(l);i.addEventListener('change',()=>handler(i.value));return i;
 }
 prefs.alpha=clamp(prefs.alpha,.35,1,1);prefs.borderWidth=clamp(prefs.borderWidth,0,12,3);
 if(!/^#[0-9a-f]{6}$/i.test(prefs.border))prefs.border=defaults.border;
 styleField('Opacitate','range',.35,1,.05,prefs.alpha,v=>{prefs.alpha=clamp(v,.35,1,1);save()});
 styleField('Contur','color',null,null,null,prefs.border,v=>{prefs.border=v;applyLayout();save()});
 styleField('Grosime','range',0,12,1,prefs.borderWidth,v=>{prefs.borderWidth=clamp(v,0,12,3);applyLayout();save()});
 const grip=document.createElement('button');grip.textContent='↘';grip.style.cssText='position:absolute;right:0;bottom:0;width:44px;height:44px;touch-action:none;display:none';slot.appendChild(grip);
 slot.style.touchAction='none';
 function setEdit(on){editing=on;edit.textContent=on?'Finalizează editarea':'Editează tactil';grip.style.display=on?'block':'none';slot.style.cursor=on?'move':'default';if(on)hide();else save()}
 edit.onclick=()=>setEdit(!editing);
 let drag=null;
 function start(e,resize){if(!editing||e.button>0)return;e.preventDefault();e.stopPropagation();const r=area.getBoundingClientRect();if(!r.width||!r.height)return;drag={id:e.pointerId,x:e.clientX,y:e.clientY,aw:r.width,ah:r.height,original:{...prefs},resize};e.currentTarget.setPointerCapture(e.pointerId)}
 function move(e){if(!drag||drag.id!==e.pointerId)return;const d=drag,o=d.original,dx=(e.clientX-d.x)*100/d.aw,dy=(e.clientY-d.y)*100/d.ah;if(d.resize){prefs.w=clamp(o.w+dx,30,100-o.x,o.w);prefs.h=clamp(o.h+dy,30,100-o.y,o.h)}else{prefs.x=clamp(o.x+dx,0,100-o.w,o.x);prefs.y=clamp(o.y+dy,0,100-o.h,o.y)}applyLayout()}
 function end(e){if(drag&&drag.id===e.pointerId){drag=null;save()}}
 slot.addEventListener('pointerdown',e=>{if(e.target!==grip)start(e,false)});grip.addEventListener('pointerdown',e=>start(e,true));
 slot.addEventListener('pointermove',move);slot.addEventListener('pointerup',end);slot.addEventListener('pointercancel',end);slot.addEventListener('lostpointercapture',end);
 const reset=document.createElement('button');reset.textContent='Reset poziție';controls.appendChild(reset);
 reset.onclick=()=>{Object.assign(prefs,{x:0,y:0,w:100,h:100});applyLayout();save()};
 function applyLayout(changed){
  prefs.w=clamp(prefs.w,30,100,100);prefs.h=clamp(prefs.h,30,100,100);
  prefs.x=clamp(prefs.x,0,70,0);prefs.y=clamp(prefs.y,0,70,0);
  if(changed==='x')prefs.w=Math.min(prefs.w,100-prefs.x);else prefs.x=Math.min(prefs.x,100-prefs.w);
  if(changed==='y')prefs.h=Math.min(prefs.h,100-prefs.y);else prefs.y=Math.min(prefs.y,100-prefs.h);
  for(const k of Object.keys(fields))fields[k].value=prefs[k];
  Object.assign(slot.style,{left:prefs.x+'%',top:prefs.y+'%',width:prefs.w+'%',height:prefs.h+'%',right:'auto',bottom:'auto',border:prefs.borderWidth+'px solid '+prefs.border,boxSizing:'border-box'});
 }
 applyLayout();
 function hide(){if(window.BIDGoogleMap)try{BIDGoogleMap.sync('{"show":false}')}catch(e){}}
 function sync(){
  if(!active||editing||!drive.classList.contains('on')||document.hidden){hide();return}
  if(!window.BIDGoogleMap){status.textContent='SDK disponibil numai în APK compatibil.';return}
  let st;try{st=JSON.parse(BIDGoogleMap.status())}catch(e){hide();return}
  if(!st.keyConfigured||st.playServices!==0){hide();status.textContent=!st.keyConfigured?'Cheia Google Maps BID lipsește.':'Google Play Services indisponibil: '+st.playServices;return}
  if(!fix||Date.now()-fixAt>15000){hide();status.textContent='Aștept poziție GPS actuală.';return}
  const outer=slot.getBoundingClientRect(),bw=prefs.borderWidth*outer.width/Math.max(1,slot.offsetWidth);
  const r={left:outer.left+bw,top:outer.top+bw,right:outer.right-bw,bottom:outer.bottom-bw,width:outer.width-2*bw,height:outer.height-2*bw};
  if(r.width<100||r.height<80||r.left<0||r.top<0||r.right>innerWidth+1||r.bottom>innerHeight+1){hide();return}
  BIDGoogleMap.sync(JSON.stringify({show:true,vw:innerWidth,vh:innerHeight,x:r.left,y:r.top,w:r.width,h:r.height,lat:fix.lat,lon:fix.lon,bearing:prefs.heading?Number(fix.bearing)||0:0,zoom:prefs.zoom,mode:prefs.mode,traffic:prefs.traffic,stationary:false,alpha:prefs.alpha}));
  status.textContent=st.detail||'Inițializare hartă.';
 }
 function save(){prefs={...prefs,mode:mode.value,zoom:Number(zoom.value),traffic:traffic.checked,heading:heading.checked};try{localStorage.setItem(key,JSON.stringify(prefs))}catch(e){status.textContent='Salvarea locală a eșuat.'}sync()}
 [mode,zoom,traffic,heading].forEach(el=>el.addEventListener('change',save));
 const oldFix=window.bidDriveFix;window.bidDriveFix=function(d){if(typeof oldFix==='function')oldFix(d);if(d&&Number.isFinite(d.lat)&&Number.isFinite(d.lon)&&d.lat>=-85&&d.lat<=85&&Math.abs(d.lon)<=180){fix=d;fixAt=Date.now();sync()}};
 const oldState=window.bidGoogleMapState;window.bidGoogleMapState=function(d){if(typeof oldState==='function')oldState(d);if(active&&d&&d.detail)status.textContent=d.detail};
 entry.onclick=()=>{driving();active=true;box.style.display='block';requestAnimationFrame(sync)};
 q('[data-close]').onclick=()=>{active=false;editing=false;drag=null;grip.style.display='none';edit.textContent='Editează tactil';box.style.display='none';hide();closeAll();theme(true)};
 new MutationObserver(()=>{if(!drive.classList.contains('on')){active=false;box.style.display='none';hide()}}).observe(drive,{attributes:true,attributeFilter:['class']});
 addEventListener('resize',sync);document.addEventListener('visibilitychange',sync);setInterval(()=>{if(active)sync()},1500);
})();
