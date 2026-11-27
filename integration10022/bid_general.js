(function(){
'use strict';
const opts=['keep_awake','system_bars'];
const native=()=>window.BID;
function read(key){try{return native().generalPreference(key)===true;}catch(_){return false;}}
function write(key,value){if(!opts.includes(key)||typeof value!=='boolean')return false;try{native().setGeneralPreference(key,value);return true;}catch(_){return false;}}
const modal=document.createElement('div');modal.id='bidGeneralModal';modal.setAttribute('role','dialog');modal.setAttribute('aria-label','Setări generale BID');
modal.style.cssText='display:none;position:fixed;inset:0;z-index:2147480000;background:#120d10f5;color:#e5d4bd;padding:4%;overflow:auto;font:20px sans-serif';
const heading=document.createElement('h2');heading.textContent='BID • Setări generale';modal.append(heading);
function button(label,fn){const b=document.createElement('button');b.textContent=label;b.style.cssText='padding:12px;margin:6px;border:1px solid #9a806c;border-radius:8px;color:#e5d4bd;background:#351c28';b.onclick=fn;modal.append(b);return b;}
function toggle(label,get,set){const row=document.createElement('label');row.style.cssText='display:block;padding:12px';const i=document.createElement('input');i.type='checkbox';i.onchange=()=>{if(!set(i.checked))i.checked=get();};row.append(i,document.createTextNode(' '+label));modal.append(row);return ()=>{i.checked=get();};}
const refresh=[toggle('Ecran activ cât timp BID este vizibil',()=>read('keep_awake'),v=>write('keep_awake',v)),toggle('Afișează barele Android în BID',()=>read('system_bars'),v=>write('system_bars',v)),toggle('Reduce animațiile temelor',()=>document.getElementById('bfReduceMotion')?.checked===true,v=>{const el=document.getElementById('bfReduceMotion');if(!el)return false;el.checked=v;el.dispatchEvent(new Event('change'));return true;})];
const p=document.createElement('p');p.textContent='Luminozitate în BID';modal.append(p);
for(const [id,label] of [['auto','Automat'],['sun','Soare'],['day','Zi'],['night','Noapte']])button(label,()=>window.bidDisplayMode(id));
button('Asistent vocal Android',()=>{try{native().openVoiceAssistant();}catch(_){}});
button('Închide',()=>{modal.classList.remove('on');modal.style.display='none';});
document.body.append(modal);
window.bidGeneralOpen=function(){refresh.forEach(f=>f());modal.classList.add('on');modal.style.display='block';};
})();