"""Extend the original backup format without exporting PIN, GPS or OEM state."""
from pathlib import Path
p=Path("app/src/main/assets/bid_system.js")
s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1, old
    s=s.replace(old,new)
replace("maxlength=\"4096\"", "maxlength=\"16384\"")
replace("Backup doar pentru preferințele BID: luminozitate, profil audio orientativ, tema ceasului și favorite.", "BID Recovery: preferințe BID și carnetul de service. Restaurarea înlocuiește datele incluse în backup. PIN-ul nu este exportat.")
anchor=" $('bidSystemExport').onclick="
start=s.index(anchor)
end=s.index("\n})();", start)
s=s[:start]+""" const serviceKey='bid.service.v1';
 const keys=(o,k)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join(',')===k;
 const integer=(v,min,max)=>v===null||Number.isInteger(v)&&v>=min&&v<=max;
 function serviceValid(v){
  return v===null||keys(v,'odo,records')&&integer(v.odo,0,1500000)&&Array.isArray(v.records)&&v.records.length===10&&v.records.every(r=>
    keys(r,'date,interval,km,months')&&integer(r.km,0,1500000)&&integer(r.interval,1,500000)&&integer(r.months,1,240)&&
    typeof r.date==='string'&&(r.date===''||/^\\d{4}-\\d{2}-\\d{2}$/.test(r.date)&&!isNaN(Date.parse(r.date))&&new Date(r.date).toISOString().slice(0,10)===r.date));
 }
 function readService(){const raw=localStorage.getItem(serviceKey);if(raw===null)return null;const v=JSON.parse(raw);if(!serviceValid(v))throw Error('Service invalid');return v}
 function restore(raw){
  if(typeof raw!=='string'||raw.length>16384)throw Error('Dimensiune invalidă');
  const d=JSON.parse(raw);
  if(d&&d.version===1){const p=validate(raw);store(p);return p}
  if(!keys(d,'format,preferences,service,version')||d.format!=='DJ88-BID-preferences'||d.version!==2||!serviceValid(d.service))throw Error('Format invalid');
  const p=validate(JSON.stringify({format:d.format,version:1,preferences:d.preferences}));
  const names=[...Object.keys(defaults),serviceKey],old=names.map(k=>[k,localStorage.getItem(k)]);
  try{store(p);if(d.service!==null)localStorage.setItem(serviceKey,JSON.stringify(d.service))}
  catch(e){for(const [k,v] of old){try{if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(_){}}throw e}
  window.dispatchEvent(new Event('bid-service-restored'));
  return p;
 }
 $('bidSystemExport').onclick=()=>{try{$('bidSystemBackup').value=JSON.stringify({format:'DJ88-BID-preferences',version:2,preferences:read(),service:readService()},null,2);$('bidSystemBackup').select();note('Backup generat. Copiază textul într-un fișier separat. Nu include PIN-ul.')}catch(_){note('Backup indisponibil: verifică datele locale.')}};
 $('bidSystemImport').onclick=()=>{try{const p=restore($('bidSystemBackup').value);if(typeof window.bidDisplayMode==='function')window.bidDisplayMode(p.bid_display_mode);render();note('Datele incluse în backup au fost restaurate. PIN-ul nu a fost modificat.')}catch(_){note('Backup invalid sau salvare indisponibilă. Nicio comandă OEM executată.');}};
"""+s[end:]
p.write_text(s)
p=Path("app/src/main/assets/bid_service.js")
s=p.read_text()
anchor="b.onclick=()=>{host.hidden=true;panel.hidden=false;render()};"
assert s.count(anchor)==1
s=s.replace(anchor,"""window.addEventListener('bid-service-restored',()=>{try{const raw=localStorage.getItem(key);if(raw!==null){state=JSON.parse(raw);if(!panel.hidden)render()}}catch(_){}});
"""+anchor)
p.write_text(s)
print("Recovery v2: preferences + service, v1 compatibility, strict field allowlist, no PIN or GPS.")
