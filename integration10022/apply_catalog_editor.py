from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1, "Missing or ambiguous: "+old[:100]
    s=s.replace(old,new,1)
replace("return {...main,...first,otherPages:others,pageOrder:order.slice()};",
"""const source=v.catalogSource;const catalogSource=source&&typeof source.id==='string'&&/^[-a-zA-Z0-9_]{1,64}$/.test(source.id)&&Number.isSafeInteger(source.revision)&&source.revision>0?{id:source.id,revision:source.revision}:null;return {...main,...first,otherPages:others,pageOrder:order.slice(),...(catalogSource?{catalogSource}:{})};""")
replace("description:typeof v.description==='string'?v.description.slice(0,500):''};",
"""description:typeof v.description==='string'?v.description.slice(0,500):'',preview:{bg:/^#[0-9a-f]{6}$/i.test(v.preview?.bg||'')?v.preview.bg:'#211820',fg:/^#[0-9a-f]{6}$/i.test(v.preview?.fg||'')?v.preview.fg:'#e4d0b6'}};""")
replace("function renderOnline(){onlineList.replaceChildren();",
"""function catalogInstalledRevision(id,themes){return themes.reduce((n,t)=>t.catalogSource?.id===id?Math.max(n,t.catalogSource.revision):n,0);}
function renderOnline(){onlineList.replaceChildren();""")
replace("row.append(label);buttonBatch('Descarcă pentru previzualizare',()=>onlineRequest(e),row);",
"""const preview=document.createElement('div');preview.style.cssText='width:160px;height:90px;border:1px solid currentColor;display:grid;place-items:center;overflow:hidden';preview.style.backgroundColor=e.preview.bg;preview.style.color=e.preview.fg;preview.textContent=e.name;preview.setAttribute('aria-label','Mostră de culori, nu captură a temei');row.append(preview,label);const revision=catalogInstalledRevision(e.id,state.themes);if(revision){const badge=document.createElement('span');badge.textContent=' Instalat: v'+revision;row.append(badge);}buttonBatch(revision&&e.revision>revision?'Previzualizează actualizarea (copie separată)':'Descarcă pentru previzualizare',()=>onlineRequest(e),row);""")
replace("const t=theme(doc.theme);t.id=uid('t');if(!confirm('Deschizi o copie nouă a temei? Ciorna nesalvată poate fi pierdută.'))return;",
"""const t=theme({...doc.theme,catalogSource:{id:p.entry.id,revision:p.entry.revision}});t.id=uid('t');const revision=catalogInstalledRevision(p.entry.id,state.themes);if(revision&&p.entry.revision>revision)t.name=(t.name.slice(0,35)+' v'+p.entry.revision).slice(0,48);if(!confirm('Deschizi o copie nouă? Tema instalată și personalizările ei rămân intacte. Ciorna nesalvată poate fi pierdută.'))return;""")
# Adjacent layer movement, only for unlocked non-native elements.
anchor="for(const [id,dir] of [['bfFront',1],['bfBack',-1],['bfDelete',0]])"
replace(anchor,"""function adjacentLayerIndex(items,index,direction){if(direction!==1&&direction!==-1)return -1;const next=index+direction;if(index<0||index>=items.length||next<0||next>=items.length)return -1;const native=e=>['external','osm','googleMap'].includes(e.type);if(items[index].locked||items[next].locked||native(items[index])||native(items[next]))return -1;return next;}
for(const [title,dir] of [['Strat +1',1],['Strat -1',-1]]){const b=document.createElement('button');b.type='button';b.textContent=title;b.onclick=()=>{if(!allowed()||!draft)return;const i=draft.elements.findIndex(e=>e.id===selected),j=adjacentLayerIndex(draft.elements,i,dir);if(j<0){message('Stratul este blocat, nativ sau la limită.');return;}checkpoint();[draft.elements[i],draft.elements[j]]=[draft.elements[j],draft.elements[i]];render();};$('bfFront').after(b);}
"""+anchor)
p.write_text(s)
