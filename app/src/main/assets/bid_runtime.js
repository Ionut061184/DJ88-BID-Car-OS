function fit(){const el=document.getElementById('stage');const s=Math.min(innerWidth/1280,innerHeight/720);el.style.transform='scale('+s+')';el.style.left=((innerWidth-1280*s)/2)+'px';el.style.top=((innerHeight-720*s)/2)+'px'}addEventListener('resize',fit);fit();
function tick(){
 const d=new Date();
 document.getElementById('clock').textContent=d.toLocaleTimeString('ro-RO',{hour:'2-digit',minute:'2-digit'});
 document.getElementById('dateLive').textContent=d.toLocaleDateString('ro-RO',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
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
 if(car){car.textContent='— V';car.title='Tensiunea mașinii: CANBUS neintegrat';}
}
refreshAndroidBattery();setInterval(refreshAndroidBattery,10000);

function statusNotice(msg){const el=document.getElementById('statusNotice');el.textContent=msg;el.style.display='block';clearTimeout(window.bidNoticeTimer);window.bidNoticeTimer=setTimeout(()=>el.style.display='none',3800)}
function canUnsupported(name){statusNotice(name+': date CANBUS încă neverificate; comanda OEM nu este simulată.')}
function mediaKey(action){if(window.BID && typeof BID.mediaKey==='function'){BID.mediaKey(action)}else statusNotice('Comanda media nu este disponibilă în browser.')}
function configureWeather(){if(window.BID && typeof BID.chooseWeatherCity==='function'){BID.chooseWeatherCity()}else statusNotice('Vremea live necesită conexiune și aplicația Android.')}
function updateWeather(city,temperature,description){let el=document.getElementById('weatherLive');el.textContent=temperature===null?'Vreme indisponibilă · '+city:description+' '+temperature+'°C · '+city;}
function updateMedia(title,playing){const el=document.getElementById('mediaLive');el.textContent=title||'Media: fără date';}
function luxury(on=true){
 document.getElementById('luxuryModal').classList.toggle('on',on);
 if(on){theme(false);document.getElementById('drive').classList.remove('on');document.getElementById('diagnosticModal').classList.remove('on');localStorage.setItem('bid_mode','luxury')}
}
function luxuryLaunch(cmd){luxury(false);launch(cmd)}
function luxuryAuto(action){luxury(false);autoLaunch(action)}
function theme(on){document.getElementById('overlay').classList.toggle('on',on)}
function closeAll(){luxury(false);document.getElementById('diagnosticModal').classList.remove('on');theme(false);document.getElementById('drive').classList.remove('on');localStorage.setItem('bid_mode','luxury')}
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
