/* Optional UI lock for personal BID preferences; never intercept OEM controls. */
(function(){
'use strict';
const system=document.getElementById('bidSystemPanel'),stage=document.getElementById('stage');
if(!system||!stage)return;
const available=()=>window.BID&&['settingsPinEnabled','settingsPinVerify','settingsPinChange'].every(k=>typeof BID[k]==='function');
const enabled=()=>{try{return available()&&BID.settingsPinEnabled()===true}catch(_){return true}};
const button=document.createElement('button');button.id='bidSecurityOpen';system.querySelector('.row').appendChild(button);
const modal=document.createElement('div');modal.id='bidSecurityPanel';modal.hidden=true;
modal.style.cssText='position:absolute;inset:0;z-index:70;background:#16090efc;padding:35px 80px;overflow:auto;color:#ffe5be;font:22px Arial';
modal.innerHTML='<h1>BID Security</h1><p id="bidSecurityInfo"></p><form id="bidSecurityForm"><label id="bidOldLabel">PIN actual <input id="bidOldPin" type="password" inputmode="numeric" maxlength="12" autocomplete="off"></label><br><label id="bidNewLabel">PIN nou (6–12 cifre) <input id="bidNewPin" type="password" inputmode="numeric" maxlength="12" autocomplete="off"></label><br><label id="bidConfirmLabel">Confirmă PIN <input id="bidConfirmPin" type="password" inputmode="numeric" maxlength="12" autocomplete="off"></label><p id="bidSecurityStatus" role="status"></p><button type="submit" id="bidSecuritySave">Confirmă</button> <button type="button" id="bidSecurityDisable">Dezactivează PIN</button> <button type="button" id="bidSecurityCancel">Înapoi</button></form><p>PIN-ul protejează configurarea favoritelor și restaurarea preferințelor BID. Nu blochează aplicațiile, comenzile originale sau luminozitatea. Dacă uiți PIN-ul, ștergerea datelor aplicației din Android îl resetează, dar șterge și datele BID. Păstrează un backup separat.</p>';
stage.appendChild(modal);
const $=id=>document.getElementById(id);
let action=null,mode='manage';
const clean=()=>{for(const k of ['bidOldPin','bidNewPin','bidConfirmPin'])$(k).value=''};
function label(){button.textContent='BID Security · '+(available()?(enabled()?'Activ':'Dezactivat'):'Indisponibil');button.disabled=!available()}
function close(){modal.hidden=true;action=null;clean();label()}
function show(next,fn){mode=next;action=fn||null;clean();$('bidSecurityStatus').textContent='';
 const on=enabled();$('bidOldLabel').hidden=!on;$('bidNewLabel').hidden=next==='verify';$('bidConfirmLabel').hidden=next==='verify';$('bidSecurityDisable').hidden=next==='verify'||!on;
 $('bidSecurityInfo').textContent=next==='verify'?'Introdu PIN-ul pentru a modifica preferințele.':on?'Protecție activă. Poți schimba sau dezactiva PIN-ul.':'Protecție dezactivată. Activează numai dacă dorești.';
 modal.hidden=false;
}
function error(r){$('bidSecurityStatus').textContent=({wrong:'PIN incorect.',wait:'Prea multe încercări. Reîncearcă după 30 secunde.',invalid:'PIN invalid. Folosește 6–12 cifre.',error:'Operațiunea nu a reușit.'})[r]||'Operațiune indisponibilă.';clean()}
button.onclick=()=>show('manage');
$('bidSecurityCancel').onclick=close;
$('bidSecurityForm').onsubmit=e=>{e.preventDefault();try{
 if(mode==='verify'){const r=BID.settingsPinVerify($('bidOldPin').value);if(r!=='ok')return error(r);const fn=action;close();if(fn)fn();return}
 const n=$('bidNewPin').value;if(!/^[0-9]{6,12}$/.test(n)||n!==$('bidConfirmPin').value){$('bidSecurityStatus').textContent='PIN-ul trebuie să conțină 6–12 cifre și să fie confirmat identic.';return}
 const r=BID.settingsPinChange($('bidOldPin').value,n);if(r!=='ok')return error(r);close()
}catch(_){error('error')}};
$('bidSecurityDisable').onclick=()=>{try{const r=BID.settingsPinChange($('bidOldPin').value,'');if(r!=='ok')return error(r);close()}catch(_){error('error')}};
let approved=false;
system.addEventListener('click',e=>{
 const target=e.target.closest('[data-favorite],#bidSystemImport');
 if(!target||approved||!enabled())return;
 e.preventDefault();e.stopImmediatePropagation();
 show('verify',()=>{approved=true;try{target.click()}finally{approved=false}})
},true);
const previous=window.closeAll;if(typeof previous==='function')window.closeAll=function(){close();return previous.apply(this,arguments)};
label();
})();
