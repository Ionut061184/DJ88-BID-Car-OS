/* QF OEM telemetry: test values only; never a certified speedometer. */
(function(){
 'use strict';
 const stage=document.getElementById('stage');
 if(!stage)return;
 const css=document.createElement('style');
 css.textContent='.qfTile{position:absolute;top:640px;width:142px;height:51px;z-index:6;border:0;border-radius:10px;background:#080609;color:#f9e7c8;font:25px Arial,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0;line-height:1.1}.qfTile small{font:12px Arial,sans-serif;color:#dfbd87}.qfTile:focus-visible{outline:2px solid #e6c080}#qfSpeedTile{left:26px}#qfFuelTile{left:1112px}#qfVehiclePanel{position:absolute;inset:0;z-index:35;background:#10060af5;padding:36px 65px;overflow:auto;color:#ffe5be}#qfVehiclePanel section{border:2px solid #c5a06a;border-radius:20px;padding:20px;background:#35121f}#qfVehicleText{white-space:pre-line;font:24px/1.5 Arial,sans-serif}';
 document.head.appendChild(css);
 const tile=(id,label)=>{const el=document.createElement('button');el.id=id;el.className='qfTile';el.setAttribute('aria-label',label+' – diagnostic CAN');const value=document.createElement('span');const caption=document.createElement('small');caption.textContent='CAN TEST';el.append(value,caption);stage.appendChild(el);el.onclick=open;return value};
 const speed=tile('qfSpeedTile','Viteză'),fuel=tile('qfFuelTile','Combustibil');
 const panel=document.createElement('div');panel.id='qfVehiclePanel';panel.hidden=true;panel.setAttribute('role','dialog');panel.setAttribute('aria-label','Diagnostic CAN-BUS OEM');
 panel.innerHTML='<section><button class="close" id="qfClose">Închide ✕</button><h1>BID Vehicle · CAN TEST</h1><p>Comparați valorile cu meniul original, numai cu mașina staționată. Sursa nu este încă autentificată.</p><div id="qfVehicleText"></div><div class="row"><button id="qfOriginal">Meniu auto original</button></div></section>';
 stage.appendChild(panel);
 document.getElementById('qfClose').onclick=()=>{panel.hidden=true};
 document.getElementById('qfOriginal').onclick=()=>{panel.hidden=true;if(window.BID&&typeof BID.open==='function')BID.open('car')};
 const oldClose=window.closeAll;if(typeof oldClose==='function')window.closeAll=function(){panel.hidden=true;return oldClose.apply(this,arguments)};
 // Preserve the original Mașină action; the two CAN tiles open this diagnostic panel.
 function open(){if(typeof window.closeAll==='function')window.closeAll();panel.hidden=false;refresh()}
 function read(){try{return window.BID&&typeof BID.qfVehicleSnapshot==='function'?JSON.parse(BID.qfVehicleSnapshot()):{}}catch(_){return {}}}
 function format(d,key,unit,max,decimal=0){const v=d[key];return d.fresh===true&&typeof d.ageMs==='number'&&d.ageMs>=0&&d.ageMs<=5000&&typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=max?v.toFixed(decimal)+' '+unit:'— '+unit}
 function diagnostic(d){
  if(d.listening!==true)return 'Receptor indisponibil'+(d.registrationError?' ('+d.registrationError+')':'');
  if(!d.messages)return 'Niciun mesaj OEM primit în sesiunea curentă.';
  if(!d.candidateFrames)return 'Mesaje primite, dar formatul nu corespunde decodorului.';
  if(d.fresh!==true||typeof d.ageMs!=='number'||d.ageMs<0||d.ageMs>5000)return 'Date expirate; așteptăm un mesaj nou.';
  return 'Pachet candidat primit; comparați cu meniul OEM.';
 }
 function refresh(){
  const d=read();speed.textContent=format(d,'speedCandidate','km/h',300);fuel.textContent=format(d,'fuelCandidate','L',100,1);
  if(!panel.hidden)document.getElementById('qfVehicleText').textContent=[
   'Receptor: '+(d.listening===true?'activ':'indisponibil'),
   'Mesaje: '+(Number.isInteger(d.messages)?d.messages:0)+' | Pachete candidate: '+(Number.isInteger(d.candidateFrames)?d.candidateFrames:0),
   diagnostic(d),
   'Ultimul pachet: '+(Number.isInteger(d.lastSize)?d.lastSize:0)+' octeți (așteptat 79)',
   'Extra absent/tip greșit: '+(d.wrongExtra||0)+' | Lungime: '+(d.wrongLength||0)+' | Antet: '+(d.wrongHeader||0),
   'Total de la pornirea aplicației: '+(d.totalMessages||0)+' mesaje / '+(d.totalCandidates||0)+' candidate',
   'Viteză: '+speed.textContent+' | Combustibil: '+fuel.textContent,
   'Turație: '+format(d,'rpmCandidate','RPM',8500),
   'Kilometraj: '+format(d,'odometerCandidate','km',1500000,1),
   'Consum: '+format(d,'consumptionCandidate','L/100 km',100,1),
   'Date experimentale; nu sunt confirmate pentru utilizare în mers.'
  ].join('\n');
 }
 refresh();setInterval(refresh,1000);
 document.addEventListener('visibilitychange',refresh);
})();
