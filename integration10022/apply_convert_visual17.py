from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old='<button id="bfAdd">Adaugă element</button>'
assert s.count(old)==1
s=s.replace(old,old+'<button id="bfConvert17">Schimbă tipul elementului ales</button>',1)
old="$('bfAdd').onclick=()=>"
assert s.count(old)==1
s=s.replace(old,"""function convertVisual17(e,target){
 const families=[['clock','date'],['speed','speedDial','speedBar','speedRing'],['text','icon','shape'],['button']];
 if(!e||e.locked||e.group||!families.some(f=>f.includes(e.type)&&f.includes(target)))return null;
 const n=element({...e,type:target});
 if(['x','y','w','h','id','action','appKey'].some(k=>n[k]!==e[k]))return null;
 return n;
}
$('bfConvert17').onclick=()=>{if(!allowed()||!draft)return;const i=draft.elements.findIndex(v=>v.id===selected);const n=convertVisual17(draft.elements[i],$('bfType').value);if(!n){message('Conversie incompatibilă sau element blocat/grupat.');return;}checkpoint();draft.elements[i]=n;render();message('Tip schimbat. Geometria și comanda păstrate.');};
"""+old,1)
p.write_text(s)
