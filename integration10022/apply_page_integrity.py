from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="function pageAllowed(){"
assert s.count(a)==1
s=s.replace(a,"function pageDeletionAllowed85(t){return !!t&&t.pageOrder.length>1&&!t.elements.some(e=>e.locked);}\n"+a,1)
a="$('bfPageDelete').disabled=order.length<2;"
assert s.count(a)==1
s=s.replace(a,"$('bfPageDelete').disabled=!pageDeletionAllowed85(draft);",1)
a="if(!pageAllowed()||draft.pageOrder.length<2||!confirm('Ștergi ecranul '+draft.pageName+'?'))return;"
assert s.count(a)==1
s=s.replace(a,"if(!pageAllowed()||!pageDeletionAllowed85(draft)||!confirm('Ștergi ecranul '+draft.pageName+'?'))return;",1)
a="checkpoint();draft.otherPages.push(other);draft.pageOrder.push(other.pageId);draft=pageView(draft,other.pageId);"
# Validate the candidate before modifying draft or undo history.
if a in s:
 assert s.count(a)==1
 s=s.replace(a,"let candidate;try{candidate=theme({...draft,otherPages:[...draft.otherPages,other],pageOrder:[...draft.pageOrder,other.pageId]});}catch(err){message('Duplicare refuzată: '+err.message);return;}checkpoint();draft=pageView(candidate,other.pageId);",1)
else:
 raise AssertionError("Page duplication anchor missing")
p.write_text(s)
(root/"tests/editor10022/test_page_integrity.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function pageDeletionAllowed85(');a.ok(i>=0);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);
const f=c.pageDeletionAllowed85;
a.equal(f(null),false);a.equal(f({pageOrder:['p'],elements:[]}),false);
a.equal(f({pageOrder:['p','q'],elements:[{locked:true}]}),false);
a.equal(f({pageOrder:['p','q'],elements:[{locked:false}]}),true);
console.log('4 page deletion safeguards passed');
""")
