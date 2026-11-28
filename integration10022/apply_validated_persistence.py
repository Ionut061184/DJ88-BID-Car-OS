from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="function persist(next){try{const before=localStorage.getItem(KEY);localStorage.setItem(KEY,JSON.stringify({version:1,...next}));state=next;"
new="function persist(next){try{const candidate=snapshot({version:1,...next});if(next.active!==candidate.active)throw Error('Tema activă este invalidă.');const serialized=JSON.stringify({version:1,...candidate});const before=localStorage.getItem(KEY);if(before===serialized){state=candidate;return true;}localStorage.setItem(KEY,serialized);state=candidate;"
assert s.count(old)==1,"Persistence anchor changed"
s=s.replace(old,new,1)
p.write_text(s)

# Repeated identical saves must not overwrite the last distinct recovery point.
t=Path(sys.argv[1])/"tests/editor10022/test_persistence_noop.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function persist(next)'),j=s.indexOf('\\n',i);a.ok(i>=0&&j>i);
const data=new Map([['main','original']]);let writes=0;
const c={KEY:'main',BACKUP:'backup',state:{},backupWarning:'',window:{},message(){},snapshot(v){return {themes:v.themes,active:v.active,applied:v.applied};},localStorage:{getItem:k=>data.get(k)||null,setItem(k,v){writes++;data.set(k,v);}}};
vm.createContext(c);vm.runInContext(s.slice(i,j),c);
const next={themes:[],active:null,applied:null};a.equal(c.persist(next),true);a.equal(data.get('backup'),'original');const before=writes;a.equal(c.persist(next),true);a.equal(writes,before);a.equal(data.get('backup'),'original');console.log('5 identical-save backup checks passed');
""")
