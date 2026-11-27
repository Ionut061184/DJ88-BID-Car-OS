from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
anchor="function refreshPrecision(){"
assert s.count(anchor)==1
s=s.replace(anchor,"""const normalized15=document.createElement('fieldset');
const normalizedTitle15=document.createElement('legend');normalizedTitle15.textContent='Geometrie relativă (%)';normalized15.append(normalizedTitle15);
const normalizedInputs15={};
for(const [key,title,base] of [['x','Stânga',W],['y','Sus',H],['w','Lățime',W],['h','Înălțime',H]]){
 const label=document.createElement('label');label.textContent=title;
 const input=document.createElement('input');input.type='number';input.min='0';input.max='100';input.step='0.1';label.append(input);normalized15.append(label);normalizedInputs15[key]=input;
 input.onchange=()=>{if(!allowed()||!draft)return;const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group)return;const n=input.valueAsNumber;if(!Number.isFinite(n))return;const candidate=element({...e,[key]:Math.round(Math.max(0,Math.min(100,n))*base/100)});checkpoint();Object.assign(e,candidate);render();};
}
$('bfControls').append(normalized15);
function refreshNormalized15(){const e=draft?.elements.find(v=>v.id===selected);for(const [key,input] of Object.entries(normalizedInputs15)){input.disabled=!e||e.locked||!!e.group;input.value=e?(100*e[key]/(['x','w'].includes(key)?W:H)).toFixed(1):'';}}
function refreshPrecision(){refreshNormalized15();""",1)
p.write_text(s)
