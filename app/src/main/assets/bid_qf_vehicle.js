/* QF OEM telemetry: test values only; never a certified speedometer. */
(function(){
 'use strict';
 const stage=document.getElementById('stage');
 if(!stage)return;
 const css=document.createElement('style');
 css.textContent='.qfTile{position:absolute;top:625px;height:73px;z-index:6;border:0;background:#080609;color:#dfbd87;font:14px Arial,sans-serif;display:flex;flex-direction:column;align-items:stretch;justify-content:center;padding:2px 5px;box-sizing:border-box;line-height:16px;text-align:left;overflow:hidden}.qfTile:focus-visible{outline:2px solid #e6c080}#qfSpeedTile{left:17px;width:178px}#qfFuelTile{left:1084px;width:190px}.qfRow{display:flex;gap:4px;align-items:center;min-height:16px;white-space:nowrap}.qfRow img{width:15px;height:15px;object-fit:contain;flex:none}.qfRow span{overflow:hidden;text-overflow:ellipsis}.qfRow[data-tone=unknown]{color:#929292}.qfRow[data-tone=unknown] img{filter:grayscale(1);opacity:.6}.qfRow[data-tone=normal]{color:#73d68b}.qfRow[data-tone=red]{color:#ff5555}.qfRow[data-tone=yellow]{color:#ffd05c}.qfTest{font:9px Arial;color:#a89a83;align-self:flex-end;line-height:10px}#qfVehiclePanel{position:absolute;inset:0;z-index:35;background:#10060af5;padding:36px 65px;overflow:auto;color:#ffe5be}#qfVehiclePanel section{border:2px solid #c5a06a;border-radius:20px;padding:20px;background:#35121f}#qfVehicleText{white-space:pre-line;font:24px/1.5 Arial,sans-serif}';
 document.head.appendChild(css);
 let icons={};
 try{if(window.BID&&typeof BID.qfVehicleIcons==='function')icons=JSON.parse(BID.qfVehicleIcons())||{};}catch(_){}
 const tile=(id,label)=>{const el=document.createElement('button');el.id=id;el.className='qfTile';el.setAttribute('aria-label',label+' – diagnostic CAN');stage.appendChild(el);el.onclick=open;return el};
 const left=tile('qfSpeedTile','Viteză, turație, combustibil'),right=tile('qfFuelTile','Kilometraj, frână de mână, temperatură, lichid parbriz');
 const row=(parent,label,icon)=>{const el=document.createElement('div');el.className='qfRow';el.dataset.tone='unknown';const img=document.createElement('img');img.alt='';img.hidden=true;const value=document.createElement('span');el.append(img,value);parent.appendChild(el);el.title=label;return {el,img,value,label,icon};};
 const speedRow=row(left,'Viteză','common_instantan_speed');
 const rpmRow=row(left,'Turație','common_engine_speed');
 const fuelRow=row(left,'Combustibil','common_oil_surplus_normal');
 const testLabel=document.createElement('small');testLabel.className='qfTest';testLabel.textContent='CAN TEST';left.appendChild(testLabel);
 const odoRow=row(right,'Kilometraj','common_driving_mile');
 const brakeRow=row(right,'Frână','common_handbrake_state_nomal');
 const tempRow=row(right,'Exterior','common_outside_temp');
 const washerRow=row(right,'Parbriz','common_cleaning_liquid_normal');
 const speed=speedRow.value,fuel=fuelRow.value;
 function paint(r,value,tone='unknown',icon=r.icon){
  r.value.textContent=r.label+': '+value;
  r.el.dataset.tone=tone;
  const uri=icons[icon];
  if(typeof uri==='string'&&uri.startsWith('data:image/png;base64,')&&/^[A-Za-z0-9+/=]+$/.test(uri.slice(22))){r.img.src=uri;r.img.hidden=false;}
  else{r.img.hidden=true;r.img.removeAttribute('src');}
 }
 const panel=document.createElement('div');panel.id='qfVehiclePanel';panel.hidden=true;panel.setAttribute('role','dialog');panel.setAttribute('aria-label','Diagnostic CAN-BUS OEM');
 panel.innerHTML='<section><button class="close" id="qfClose">Închide ✕</button><h1>BID Vehicle · CAN TEST</h1><p>Comparați valorile cu meniul original, numai cu mașina staționată. Sursa nu este încă autentificată.</p><div class="row"><button id="qfAudit" type="button">Pornește test recepție (120 s)</button><button id="qfOriginal" type="button">Meniu auto original</button><button id="qfBodyOriginal" type="button">Informații CAN originale</button></div><div class="row"><button type="button" id="qfExportOem">Salvează APK CANBUS original pentru analiză</button></div><p id="qfAuditStatus" role="status" aria-live="polite" style="font: bold 24px Arial; color:#ffd05c">Test nepornit.</p><div id="qfVehicleText"></div></section>';
 stage.appendChild(panel);
 const auditButton=document.getElementById('qfAudit'), auditStatus=document.getElementById('qfAuditStatus');
 document.getElementById('qfExportOem').onclick=()=>{try{if(window.BID&&typeof BID.qfExportInstalledApk==='function')BID.qfExportInstalledApk();else alert('Exportul OEM nu este disponibil în acest build.');}catch(e){alert('Nu s-a putut deschide salvarea APK.');}};
 let auditRequestedAt=0, auditError='';
 auditButton.onclick=()=>{
  auditError='';auditRequestedAt=0;
  if(!window.BID||typeof BID.qfBeginBodyAudit!=='function'){auditError='Comanda Android pentru test lipsește.';auditStatus.textContent=auditError;return;}
  auditRequestedAt=Date.now();auditButton.disabled=true;auditStatus.textContent='Solicitare trimisă. Se așteaptă confirmarea receptorului…';
  try{BID.qfBeginBodyAudit();}catch(e){auditRequestedAt=0;auditError='Comanda Android a eșuat.';auditButton.disabled=false;auditStatus.textContent=auditError;}
 };
 document.getElementById('qfClose').onclick=()=>{panel.hidden=true};
 document.getElementById('qfOriginal').onclick=()=>{panel.hidden=true;if(window.BID&&typeof BID.open==='function')BID.open('car')};
 document.getElementById('qfBodyOriginal').onclick=()=>{panel.hidden=true;if(window.BID&&typeof BID.open==='function')BID.open('canbus')};
 const oldClose=window.closeAll;if(typeof oldClose==='function')window.closeAll=function(){panel.hidden=true;return oldClose.apply(this,arguments)};
 // Preserve the original Mașină action; the two CAN tiles open this diagnostic panel.
 function open(){if(typeof window.closeAll==='function')window.closeAll();panel.hidden=false;refresh()}
 function read(){try{return window.BID&&typeof BID.qfVehicleSnapshot==='function'?JSON.parse(BID.qfVehicleSnapshot()):{}}catch(_){return {}}}
 function format(d,key,unit,max,decimal=0){const v=d[key];return d.fresh===true&&typeof d.ageMs==='number'&&d.ageMs>=0&&d.ageMs<=5000&&typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=max?v.toFixed(decimal)+' '+unit:'— '+unit}
 function flag(d,key,on,off){
  return d.fresh===true&&typeof d.ageMs==='number'&&d.ageMs>=0&&d.ageMs<=5000&&typeof d[key]==='boolean'?(d[key]?on:off):'—';
 }
 function outsideTemp(d){
  const v=d.outsideTemperatureCandidate,a=d.outsideTemperatureAgeMs;
  return d.outsideTemperatureFresh===true&&Number.isFinite(a)&&a>=0&&a<=120000&&Number.isFinite(v)&&v>=-60&&v<=85?v.toFixed(1)+' °C':'— °C';
 }
 function freshCabin(d,kind){
  const a=d[kind+'AgeMs'];return d[kind+'Fresh']===true&&Number.isFinite(a)&&a>=0&&a<=30000;
 }
 function climateValue(d,key){
  const v=d[key];return freshCabin(d,'climate')&&typeof v==='string'&&/^(LO|HI|[0-9]{1,3}[.][05])$/.test(v)?v:'—';
 }
 function doorsText(d){
  const n=d.doorMaskCandidate;
  if(!freshCabin(d,'door')||!Number.isInteger(n)||n<0||n>252||(n&3)!==0)return '—';
  return [[128,'față stânga'],[64,'față dreapta'],[32,'spate stânga'],[16,'spate dreapta'],[8,'hayon'],[4,'capotă']].map(([m,label])=>label+': '+((n&m)?'deschis':'închis')).join(' | ');
 }
 function recent(d,k){const a=d[k+'AgeMs'];return d[k+'Fresh']===true&&Number.isFinite(a)&&a>=0&&a<=5000;}
 function radarText(d){
  const v=d.radarLevelsCandidate;
  if(!recent(d,'radar')||!Array.isArray(v)||v.length!==20)return '—';
  return v.map(n=>Number.isInteger(n)&&n>=0&&n<255?String(n):'—').join(' / ');
 }
 function registryStatus(d){
  switch(d.bodyRegistryState){
   case 'listed':return 'Registru OEM: BID înregistrat.';
   case 'not_listed':return 'Registru OEM: BID nu este înregistrat.';
   case 'absent':return 'Registru OEM: absent sau gol.';
   case 'unreadable':return 'Registru OEM: inaccesibil.';
   default:return 'Registru OEM: stare necunoscută.';
  }
 }
 function shareStatus(d){
  switch(d.bodyShareState){
   case 'enabled': return 'Partajare caroserie: activată pentru BID (livrarea rămâne de verificat).';
   case 'disabled': return 'Partajare caroserie: dezactivată pentru BID.';
   case 'absent': return 'Partajare caroserie: cheie OEM absentă pentru BID.';
   case 'unreadable': return 'Partajare caroserie: setarea nu poate fi citită.';
   default: return 'Partajare caroserie: stare necunoscută.';
  }
 }
 function globalShareStatus(d){
  const values={enabled:'activă (cel puțin un client OEM)',disabled:'inactivă (niciun client activ)',unknown:'necunoscută',unreadable:'inaccesibilă'};
  return 'Partajare globală caroserie: '+(values[d.globalBodyShareState]||'necunoscută')+'.';
 }
 function remoteModeStatus(d){
  const values={app:'aplicații (0)',app_default:'aplicații (implicit)',system:'sistem (1)',unknown:'necunoscut',unreadable:'inaccesibil'};
  return 'Mod SDK configurat: '+(values[d.remoteDemandMode]||'necunoscut')+'; BID nu inițializează SDK.';
 }
 function diagnostic(d){
  if(d.listening!==true)return 'Receptor indisponibil'+(d.registrationError?' ('+d.registrationError+')':'');
  if(!d.messages)return 'Niciun mesaj OEM primit în sesiunea curentă.';
  if(d.lastPacketState==='empty_body')return 'Pachet caroserie fără informații utile; valorile au fost retrase.';
  if(!d.candidateFrames)return 'Mesaje primite, dar formatul nu corespunde decodorului.';
  if(d.fresh!==true||typeof d.ageMs!=='number'||d.ageMs<0||d.ageMs>5000)return 'Date expirate; așteptăm un mesaj nou.';
  return 'Pachet candidat primit; comparați cu meniul OEM.';
 }
 function refresh(){
  const d=read();
  if(d.auditActive===true){
   auditRequestedAt=0;auditError='';auditButton.disabled=true;
   auditStatus.textContent='Test activ: '+(d.auditRemainingSeconds||0)+' s. '+(d.listening===true?'Receptor activ. Deschideți meniul OEM și reveniți.':'Receptor indisponibil: '+(d.registrationError||'cauză necunoscută'));
  }else if(auditRequestedAt){
   if(Date.now()-auditRequestedAt>=5000){auditRequestedAt=0;auditError='Android nu a confirmat pornirea testului în 5 s.';auditButton.disabled=false;auditStatus.textContent=auditError;}
  }else{
   auditButton.disabled=false;auditStatus.textContent=auditError||(d.auditStarted?'Test încheiat. Consultați contoarele.':'Test nepornit.');
  }
  const speedValue=format(d,'speedCandidate','km/h',300),fuelValue=format(d,'fuelCandidate','L',100,1);
  const rpmValue=format(d,'rpmCandidate','RPM',8500),odoValue=format(d,'odometerCandidate','km',1500000,0),tempValue=outsideTemp(d);
  const dataTone=v=>v.startsWith('—')?'unknown':'candidate';
  paint(speedRow,speedValue,dataTone(speedValue));paint(rpmRow,rpmValue,dataTone(rpmValue));paint(fuelRow,fuelValue,dataTone(fuelValue));
  paint(odoRow,odoValue,dataTone(odoValue));paint(tempRow,tempValue,dataTone(tempValue));
  // Do not display a reassuring green or warning state until the installed OEM mapping has been verified.
  const verified=d.verified===true;
  const b=verified?flag(d,'parkingBrakeCandidate','Trasă','Normală'):'—';
  const w=verified?flag(d,'washerFlagCandidate','Nivel scăzut','Normal'):'—';
  paint(brakeRow,b,b==='Trasă'?'red':b==='Normală'?'normal':'unknown',b==='Trasă'?'common_handbrake_state_warn':brakeRow.icon);
  paint(washerRow,w,w==='Nivel scăzut'?'yellow':w==='Normal'?'normal':'unknown',w==='Nivel scăzut'?'common_cleaning_liquid_warn':washerRow.icon);
  if(!panel.hidden)document.getElementById('qfVehicleText').textContent=[
   'Receptor: '+(d.listening===true?'activ':'indisponibil'),
   'Mesaje: '+(Number.isInteger(d.messages)?d.messages:0)+' | Pachete candidate: '+(Number.isInteger(d.candidateFrames)?d.candidateFrames:0),
   'Test temporar: '+(d.auditStarted?(d.auditActive?'activ, '+(d.auditRemainingSeconds||0)+' s':'încheiat'):'nepornit'),
   'Mesaje/pachete înainte: '+(d.auditBeforeMessages||0)+' / '+(d.auditBeforeValid||0),
   'Mesaje/pachete cât BID nu era în prim-plan: '+(d.auditAwayMessages||0)+' / '+(d.auditAwayValid||0),
   'Mesaje/pachete după revenire: '+(d.auditAfterMessages||0)+' / '+(d.auditAfterValid||0),
   'În test: deschideți manual secțiunea OEM, reveniți în BID în 120 s. Contorul nu identifică pagina OEM.',
   diagnostic(d),
   'CANBUS OEM instalat: '+(d.oemCanbusVersion||'indisponibil'),
   'Diagnostic livrare: '+(d.bodyDeliveryState||'necunoscut'),
   'Drept scriere setări globale: '+(d.globalSettingsWriteGranted===true?'da':'nu')+' (BID nu scrie setări globale).',
   'Voltaj antet: proprietate QF; tensiune caroserie OEM: sursă separată încă neidentificată.',
   globalShareStatus(d),
   remoteModeStatus(d),
   shareStatus(d),
   registryStatus(d),
   'Pachet BID: '+(typeof d.bodySharePackage==='string'?d.bodySharePackage:'necunoscut'),
   'Ultimul pachet: '+(Number.isInteger(d.lastSize)?d.lastSize:0)+' octeți (caroserie 79, climatizare 21, uși 3)',
   'Extra absent/tip greșit: '+(d.wrongExtra||0)+' | Lungime: '+(d.wrongLength||0)+' | Antet: '+(d.wrongHeader||0),
   'Total de la pornirea aplicației: '+(d.totalMessages||0)+' mesaje / '+(d.totalCandidates||0)+' candidate',
   'Viteză: '+speedValue+' | Combustibil: '+fuelValue,
   'Temperatură exterioară OEM (candidat): '+outsideTemp(d),
   'Mesaje temperatură: '+(d.temperatureMessages||0),
   'Turație: '+format(d,'rpmCandidate','RPM',8500),
   'Kilometraj: '+format(d,'odometerCandidate','km',1500000,1),
   'Consum: '+format(d,'consumptionCandidate','L/100 km',100,1),
   'Frână de mână (candidat): '+flag(d,'parkingBrakeCandidate','activă','inactivă'),
   'Centură șofer (candidat): '+flag(d,'driverBeltUnfastenedCandidate','necuplată','cuplată'),
   'Lichid parbriz (bit OEM, sens de verificat): '+flag(d,'washerFlagCandidate','1','0'),
   'Climatronic (candidat, unitate numerică neconfirmată): '+climateValue(d,'climateLeft')+' / '+climateValue(d,'climateRight'),
   'Uși și capace (candidat): '+doorsText(d),
   'Mesaje climatizare/uși: '+(d.climateMessages||0)+' / '+(d.doorMessages||0),
   'Partajare climatizare/uși: '+(d.climateShareState||'necunoscut')+' / '+(d.doorShareState||'necunoscut'),
   'Radar (niveluri brute, candidat): '+radarText(d),
   'Volan (valoare brută, nu grade): '+(recent(d,'steering')&&Number.isInteger(d.steeringRawCandidate)?d.steeringRawCandidate:'—'),
   'Ultimul eveniment marșarier: '+(recent(d,'reverse')&&typeof d.reverseEventCandidate==='boolean'?(d.reverseEventCandidate?'START':'STOP'):'—'),
   'Mesaje radar/volan/marșarier: '+(d.radarMessages||0)+' / '+(d.steeringMessages||0)+' / '+(d.reverseMessages||0),
   'Partajare radar: '+(d.radarShareState||'necunoscut'),
   'Pachete caroserie goale: '+(d.emptyBody||0),
   'Date experimentale; nu sunt confirmate pentru utilizare în mers.'
  ].join('\n');
 }
 let poll=null;
 function visibility(){
  if(poll!==null){clearInterval(poll);poll=null;}
  if(!document.hidden){refresh();poll=setInterval(refresh,1000);}
 }
 visibility();
 document.addEventListener('visibilitychange',visibility);
})();
