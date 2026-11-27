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
a="geometry(n,e,editing);"
assert s.count(a)==1
s=s.replace(a,a+"if(e.border)n.style.borderColor=e.borderColor+Math.round(e.borderAlpha*2.55).toString(16).padStart(2,'0');")
p.write_text(s)

# Extend existing schema assertions without removing any previous checks.
t=Path(sys.argv[1])/"tests/editor10022/test_advanced.js"
test=t.read_text()
import re
test,count=re.subn(r'(refreshSeconds\s*:\s*\d+)(\s*,\s*actionLocked\s*:)',r'\1,borderAlpha:100\2',test)
assert count>=1,"Expected advanced schema test not found"
t.write_text(test)
