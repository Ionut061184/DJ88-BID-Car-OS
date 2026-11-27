from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
replace("let gridMode56=false,gridPage56=0;", """let gridMode56=false,gridPage56=0,gridColumnCount56=3;
try{const p=JSON.parse(localStorage.getItem(pickerKey56+'_layout')||'null');if(p){gridMode56=p.grid===true;gridColumnCount56=[2,3,4].includes(p.cols)?p.cols:3;}}catch(_){}
function saveGridLayout56(){try{localStorage.setItem(pickerKey56+'_layout',JSON.stringify({grid:gridMode56,cols:gridColumnCount56}));}catch(_){message('Aspectul listei nu a putut fi salvat.');}}""")
replace("gridToggle56.textContent='Grilă aplicații';","gridToggle56.textContent=gridMode56?'Listă aplicații':'Grilă aplicații';")
replace("gridCols56.value='3';","gridCols56.value=String(gridColumnCount56);")
replace("gridCols56.onchange=()=>{gridPage56=0;filterInstalled();};","gridCols56.onchange=()=>{if(!allowed()){gridCols56.value=String(gridColumnCount56);return;}gridColumnCount56=Number(gridCols56.value);gridPage56=0;saveGridLayout56();filterInstalled();};")
replace("gridMode56=!gridMode56;gridPage56=0;","gridMode56=!gridMode56;gridPage56=0;saveGridLayout56();")
replace("$('bfAppSearch').oninput=filterInstalled;","$('bfAppSearch').oninput=()=>{gridPage56=0;filterInstalled();};")
replace("b.onclick=()=>{gridPage56+=step;renderGrid56(apps);};","b.onclick=()=>{if(!allowed())return;gridPage56+=step;renderGrid56(apps);};")
p.write_text(s)
