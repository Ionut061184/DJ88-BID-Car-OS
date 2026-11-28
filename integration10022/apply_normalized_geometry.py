from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
anchor="function refreshPrecision(){"
assert s.count(anchor)==1
s=s.replace(anchor,"""const normalized15=document.createElement('fieldset');
const normalizedTitle15=document.createElement('legend');normalizedTitle15.textContent='Geometrie relativă (%)';normalized15.append(normalizedTitle15);
const normalizedInputs15={};
function percentPixels15(n,base){return Number.isFinite(n)&&Number.isFinite(base)&&base>0?Math.round(Math.max(0,Math.min(100,n))*base/100):null;}
for(const [key,title,base] of [['x','Stânga',W],['y','Sus',H],['w','Lățime',W],['h','Înălțime',H]]){
 const label=document.createElement('label');label.textContent=title;
 const input=document.createElement('input');input.type='number';input.min='0';input.max='100';input.step='0.1';label.append(input);normalized15.append(label);normalizedInputs15[key]=input;
 input.onchange=()=>{if(!allowed()||!draft)return;const e=draft.elements.find(v=>v.id===selected);if(!e||e.locked||e.group)return;const n=percentPixels15(input.valueAsNumber,base);if(n===null)return;let candidate;try{candidate=element({...e,[key]:n});}catch(err){message('Geometrie invalidă');refreshNormalized15();return;}if(candidate[key]===e[key]){refreshNormalized15();return;}checkpoint();Object.assign(e,candidate);render();};
}
$('bfControls').append(normalized15);
function refreshNormalized15(){const e=draft?.elements.find(v=>v.id===selected);for(const [key,input] of Object.entries(normalizedInputs15)){input.disabled=!e||e.locked||!!e.group;input.value=e?(100*e[key]/(['x','w'].includes(key)?W:H)).toFixed(1):'';}}
function refreshPrecision(){refreshNormalized15();""",1)
p.write_text(s)

t=Path(sys.argv[1])/"tests/editor10022/test_normalized_geometry.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function percentPixels15(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.percentPixels15;
a.equal(f(50,1280),640);a.equal(f(25,720),180);a.equal(f(-5,1280),0);a.equal(f(105,720),720);a.equal(f(NaN,720),null);a.equal(f(Infinity,720),null);a.equal(f(10,0),null);a.equal(f(0.1,1280),1);console.log('8 normalized geometry checks passed');
""")
