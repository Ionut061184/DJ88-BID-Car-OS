from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="function persist(next){try{const before=localStorage.getItem(KEY);localStorage.setItem(KEY,JSON.stringify({version:1,...next}));state=next;"
new="function persist(next){try{const candidate=snapshot({version:1,...next});if(next.active!==candidate.active)throw Error('Tema activă este invalidă.');const serialized=JSON.stringify({version:1,...candidate});const before=localStorage.getItem(KEY);localStorage.setItem(KEY,serialized);state=candidate;"
assert s.count(old)==1,"Persistence anchor changed"
s=s.replace(old,new,1)
p.write_text(s)
