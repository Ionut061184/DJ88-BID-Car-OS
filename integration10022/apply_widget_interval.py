from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="if(!interval||!n.dataset.bidRefreshAt||now-Number(n.dataset.bidRefreshAt)>=interval)"
b="if(bidRefreshDue63(interval,n.dataset.bidRefreshInterval,n.dataset.bidRefreshAt,now))"
assert s.count(a)==1
s=s.replace(a,b)
a="n.dataset.bidRefreshAt=String(now);"
assert s.count(a)==1
s=s.replace(a,a+"n.dataset.bidRefreshInterval=String(interval);")
anchor="function refreshPrecision(){"
assert s.count(anchor)==1
s=s.replace(anchor,"function bidRefreshDue63(interval,previous,at,now){const last=Number(at);return !interval||previous!==String(interval)||at==null||at===''||!Number.isFinite(last)||!Number.isFinite(now)||now<last||now-last>=interval;}\n"+anchor,1)
p.write_text(s)
t=root/"tests/editor10022/test_advanced.js"
with t.open("a") as f:
 f.write("\nfor(const type of ['clock','date','weather','battery','wifi','bluetooth','cell']){eq(c.advancedRefresh({type,refreshSeconds:1}),1000);eq(c.advancedRefresh({type,refreshSeconds:60}),60000);}\nconsole.log('14 additional widget interval checks passed');\n")

t=root/"tests/editor10022/test_refresh_due.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function bidRefreshDue63(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.bidRefreshDue63;
a.equal(f(1000,'1000','100',1099),false);a.equal(f(1000,'1000','100',1100),true);a.equal(f(1000,'2000','100',101),true);a.equal(f(1000,'1000','invalid',101),true);a.equal(f(1000,'1000','200',100),true);a.equal(f(1000,'1000',undefined,100),true);a.equal(f(0,'0','100',100),true);a.equal(f(1000,'1000','0',999),false);console.log('8 widget scheduling regression checks passed');
""")
