"""Expose the existing favorite preferences in the main BID menu; no new permissions."""
from pathlib import Path
p=Path("app/src/main/assets/bid_system.js")
s=p.read_text()
anchor=" function close(){panel.hidden=true;}"
assert s.count(anchor)==1
s=s.replace(anchor,""" window.bidQuickStartRender=function(container){
  container.replaceChildren();
  const heading=document.createElement('strong');
  heading.textContent='BID Quick Start';
  container.appendChild(heading);
  for(const key of read().bid_favorites){
   const b=document.createElement('button');
   b.textContent=choices[key];b.dataset.quickFavorite=key;b.disabled=!has('open');
   b.onclick=()=>{try{BID.open(key);window.closeAll()}catch(_){status.textContent='Aplicația nu a putut fi deschisă.'}};
   container.appendChild(b);
  }
  const config=document.createElement('button');config.textContent='Configurează favorite';config.id='bidQuickConfig';config.onclick=()=>window.bidSystemOpen();container.appendChild(config);
  const status=document.createElement('span');status.setAttribute('role','status');container.appendChild(status);
 };
"""+anchor)
p.write_text(s)
p=Path("app/src/main/assets/bid_smart.js")
s=p.read_text()
old='<div class="row" id="bidSmartActions"></div>'
assert s.count(old)==1
s=s.replace(old,old+'<div class="row" id="bidQuickStart" style="margin-top:14px"></div>')
old='  panel.hidden=false;refresh();'
assert s.count(old)==1
s=s.replace(old,"  if(typeof window.bidQuickStartRender==='function')window.bidQuickStartRender($('bidQuickStart'));\n"+old)
p.write_text(s)
print("Quick Start uses existing favorites and native launch actions; original grid unchanged.")
