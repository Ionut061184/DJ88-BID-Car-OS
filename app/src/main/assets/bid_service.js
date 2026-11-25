/* Local maintenance log. No trip tracking, GPS, network or unverified CAN input. */
(function(){
'use strict';
const host=document.getElementById('qfVehiclePanel'),stage=document.getElementById('stage');
if(!host||!stage)return;
const key='bid.service.v1';
const items=[['Ulei motor',10000,12],['Filtru ulei',10000,12],['Filtru aer',15000,null],['Filtru motorină',30000,null],['Filtru polen',15000,null],['Distribuție',null,null],['Ulei Haldex 4×4',null,null],['Lichid de frână',null,24],['Antigel',null,null],['Baterie',null,null]];
const empty=()=>({odo:null,records:items.map(x=>({km:null,date:'',interval:x[1],months:x[2]}))});
let state=empty();
const number=(s,min,max)=>s===''?null:(Number.isInteger(Number(s))&&Number(s)>=min&&Number(s)<=max?Number(s):NaN);
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s).toISOString().slice(0,10)===s;
const today=()=>{const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')};
const valid=(v,a,b)=>v===null||Number.isInteger(v)&&v>=a&&v<=b;
try{const v=JSON.parse(localStorage.getItem(key));if(v&&valid(v.odo,0,1500000)&&Array.isArray(v.records)&&v.records.length===items.length&&v.records.every(r=>r&&valid(r.km,0,1500000)&&valid(r.interval,1,500000)&&valid(r.months,1,240)&&(r.date===''||validDate(r.date))))state=v}catch(_){}
const b=document.createElement('button');b.id='bidServiceOpen';b.textContent='BID Service';host.querySelector('.row').appendChild(b);
const panel=document.createElement('div');panel.id='bidServicePanel';panel.hidden=true;
panel.style.cssText='position:absolute;inset:0;z-index:36;background:#16090e;color:#ffe5be;padding:25px 45px;overflow:auto;font:18px Arial';
panel.innerHTML='<button id="bidServiceClose">Înapoi</button><h1>BID Service</h1><p>Intervalele sunt orientative și editabile; verifică manualul și codul motorului. Kilometraj manual.</p><label>Kilometraj actual <input id="bidServiceOdo" type="number" min="0" max="1500000" inputmode="numeric"></label> <button id="bidServiceSaveOdo">Salvează</button><p id="bidServiceMessage" role="status"></p><div id="bidServiceRows"></div>';
stage.appendChild(panel);
const $=id=>document.getElementById(id);
const message=s=>{$('bidServiceMessage').textContent=s};
function save(next){try{localStorage.setItem(key,JSON.stringify(next));state=next;return true}catch(_){message('Salvarea locală a eșuat.');return false}}
function dueDate(s,m){const d=new Date(s+'T00:00:00Z');const day=d.getUTCDate();d.setUTCDate(1);d.setUTCMonth(d.getUTCMonth()+m);const end=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();d.setUTCDate(Math.min(day,end));return d.toISOString().slice(0,10)}
function status(r){let checks=[],unknown=false;
 if(r.interval!==null){if(r.km===null||state.odo===null||state.odo<r.km)unknown=true;else{let n=r.km+r.interval-state.odo;checks.push([n<=0?2:n<=1000?1:0,n+' km'])}}
 if(r.months!==null){if(!r.date||r.date>today())unknown=true;else{let end=dueDate(r.date,r.months),n=Math.round((Date.parse(end)-Date.parse(today()))/86400000);checks.push([n<=0?2:n<=30?1:0,end])}}
 let level=checks.length?Math.max(...checks.map(x=>x[0])):-1;
 if(unknown&&level<1)level=-1;
 return {label:level===2?'Depășit / scadent':level===1?'Se apropie':level===0?'În termen':'Neverificat / fără termen',color:level===2?'#ff9e91':level===1?'#f9d477':level===0?'#a0e2a8':'#c4b7b8',detail:checks.map(x=>x[1]).join(' · ')+(unknown?' · date incomplete':'')};
}
function render(){ $('bidServiceOdo').value=state.odo??'';const rows=$('bidServiceRows');rows.replaceChildren();items.forEach((item,i)=>{
 const r=state.records[i],st=status(r),row=document.createElement('section');row.style.cssText='padding:12px;border-top:1px solid #826344;display:flex;flex-wrap:wrap;align-items:center;gap:10px';
 const name=document.createElement('strong');name.textContent=item[0];name.style.width='150px';row.appendChild(name);
 const field=(label,type,value)=>{const l=document.createElement('label');l.textContent=label+' ';const el=document.createElement('input');el.type=type;el.value=value??'';el.style.width=type==='date'?'140px':'90px';l.appendChild(el);row.appendChild(l);return el};
 const km=field('Ultimul km','number',r.km),date=field('Data','date',r.date),interval=field('Interval km','number',r.interval),months=field('Luni','number',r.months);
 const info=document.createElement('span');info.textContent=st.label+' '+st.detail;info.style.color=st.color;row.appendChild(info);
 const commit=(done)=>{const next=JSON.parse(JSON.stringify(state));const k=done?state.odo:number(km.value,0,1500000),d=done?today():date.value,iv=number(interval.value,1,500000),mo=number(months.value,1,240);
 if((done&&k===null)||[k,iv,mo].some(Number.isNaN)||(d&&(!validDate(d)||d>today()))||(k!==null&&state.odo!==null&&k>state.odo)){message('Verifică kilometrajul, data și intervalele.');return}
 next.records[i]={km:k,date:d,interval:iv,months:mo};if(save(next)){render();message('Salvat local: '+item[0])}};
 for(const [label,done] of [['Salvează',false],['Schimb efectuat',true]]){const btn=document.createElement('button');btn.textContent=label;btn.onclick=()=>commit(done);row.appendChild(btn)}
 rows.appendChild(row);
 })}
$('bidServiceSaveOdo').onclick=()=>{const n=number($('bidServiceOdo').value,0,1500000);if(n===null||Number.isNaN(n)||state.odo!==null&&n<state.odo){message('Kilometraj invalid sau mai mic decât cel salvat.');return}if(save({...state,odo:n})){render();message('Kilometraj salvat.')}};
b.onclick=()=>{host.hidden=true;panel.hidden=false;render()};
$('bidServiceClose').onclick=()=>{panel.hidden=true;host.hidden=false};
const old=window.closeAll;if(typeof old==='function')window.closeAll=function(){panel.hidden=true;return old.apply(this,arguments)};
})();
