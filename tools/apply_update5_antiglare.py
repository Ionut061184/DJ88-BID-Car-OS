"""Apply the approved Anti-Glare improvement after baseline verification."""
from pathlib import Path
p=Path("app/src/main/assets/bid_adaptive.js")
s=p.read_text()
anchor=" if(effective!==applied){"
assert s.count(anchor)==1
s=s.replace(anchor, """ // Anti-Glare: darken only the MASTER background in strong light.
 // Keep the native window brightness at sun mode; controls stay readable.
 const stage=document.getElementById('stage');
 if(stage){
  stage.style.backgroundColor=effective==='sun'?'#b9b9b9':'#090609';
  stage.style.backgroundBlendMode=effective==='sun'?'multiply':'normal';
  stage.dataset.bidAntiGlare=effective==='sun'?'active':'inactive';
 }
"""+anchor)
p.write_text(s)
print("Anti-Glare patch applied: no artwork, permissions or OEM settings changed.")
