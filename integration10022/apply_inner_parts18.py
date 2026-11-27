from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
replace("return {...advancedFields(v),id:v.id,type:v.type", "return {...advancedFields(v),hideInnerLabel:v.hideInnerLabel===true,hideInnerGraphic:v.hideInnerGraphic===true,id:v.id,type:v.type")
replace("if(bidMaskSupported(e)){for(const child of n.children)", "if(bidMaskSupported(e)){if(e.hideInnerLabel)label.hidden=true;if(e.hideInnerGraphic)for(const child of n.querySelectorAll('.bfGlyph,.bfAutoArt,[data-bid-gauge]'))child.hidden=true;for(const child of n.children)")
replace("function refreshPrecision(){", """function toggleInner18(k){
 if(!allowed()||!draft)return;
 const e=draft.elements.find(v=>v.id===selected);
 if(!e||e.locked||!bidMaskSupported(e))return;
 checkpoint();e[k]=!e[k];render();
}
const inner18=document.createElement('div');
for(const [k,title] of [['hideInnerLabel','Ascunde/arată textul interior'],['hideInnerGraphic','Ascunde/arată grafica interioară']]){
 const b=document.createElement('button');b.textContent=title;b.type='button';b.onclick=()=>toggleInner18(k);inner18.append(b);
}
$('bfControls').append(inner18);
function refreshPrecision(){""")
p.write_text(s)
