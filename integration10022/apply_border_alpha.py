from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="refreshSeconds:n(v.refreshSeconds,1,1,60),"
b=a+"borderAlpha:n(v.borderAlpha,100,0,100),"
assert s.count(a)==1
s=s.replace(a,b)
a="['bfBorderColor','borderColor'],"
assert s.count(a)==1
s=s.replace(a,a+"['bfBorderAlpha','borderAlpha'],")
a="const tintLabel=document.createElement('label');"
assert s.count(a)==1
s=s.replace(a,"const borderAlphaLabel=document.createElement('label');borderAlphaLabel.textContent='Opacitate contur';const borderAlphaInput=document.createElement('input');borderAlphaInput.type='range';borderAlphaInput.min='0';borderAlphaInput.max='100';borderAlphaInput.id='bfBorderAlpha';borderAlphaLabel.append(borderAlphaInput);$('bfBorderColor').closest('label').after(borderAlphaLabel);"+a)
anchor="function refreshPrecision(){"
assert s.count(anchor)==1
s=s.replace(anchor,"function bidBorderHex(value){const x=Number(value);return Math.round(Math.max(0,Math.min(100,Number.isFinite(x)?x:100))*255/100).toString(16).padStart(2,'0');}\n"+anchor,1)
a="geometry(n,e,editing);"
assert s.count(a)==1
s=s.replace(a,a+"if(e.border)n.style.borderColor=e.borderColor+bidBorderHex(e.borderAlpha);")
p.write_text(s)

# Extend existing schema assertions without removing any previous checks.
t=Path(sys.argv[1])/"tests/editor10022/test_advanced.js"
test=t.read_text()
import re
test,count=re.subn(r'(refreshSeconds\s*:\s*\d+)(\s*,\s*actionLocked\s*:)',r'\1,borderAlpha:100\2',test)
assert count>=1,"Expected advanced schema test not found"
t.write_text(test)

t=Path(sys.argv[1])/"tests/editor10022/test_border_alpha.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function bidBorderHex(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.bidBorderHex;
a.equal(f(0),'00');a.equal(f(50),'80');a.equal(f(100),'ff');a.equal(f(-1),'00');a.equal(f(101),'ff');a.equal(f(NaN),'ff');a.equal(f(10),'1a');console.log('7 border opacity checks passed');
""")
