from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="if(items[index].locked||items[next].locked||native(items[index])||native(items[next]))return -1;"
b="if(items[index].locked||items[next].locked||items[index].group||items[next].group)return -1;if((native(items[index])||native(items[next]))&&!(items[index].type==='external'&&items[next].type==='external'))return -1;"
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s)
# Exercise the exact function from the patched editor.
t=Path(sys.argv[1])/"tests/editor10022/test_native_layer_controls.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const start=s.indexOf('function adjacentLayerIndex('),end=s.indexOf('\\n',start);
const c={};vm.createContext(c);vm.runInContext(s.slice(start,end),c);
const f=c.adjacentLayerIndex,w={type:'external'},h={type:'text'};
a.equal(f([w,w],0,1),1);a.equal(f([w,w],1,-1),0);
a.equal(f([w,h],0,1),-1);a.equal(f([w,{type:'googleMap'}],0,1),-1);
a.equal(f([w,{...w,locked:true}],0,1),-1);
a.equal(f([{...w,group:'g'},w],0,1),-1);
a.equal(f([h,h],0,1),1);a.equal(f([w,w],0,-1),-1);
console.log('8 native layer control checks passed');
""")
