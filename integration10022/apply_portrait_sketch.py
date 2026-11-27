from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="function refreshPages(){"
assert s.count(a)==1
s=s.replace(a,"""const portraitButton=document.createElement('button');
portraitButton.type='button';portraitButton.textContent='Schiță verticală 9:16';
portraitButton.onclick=()=>{
 if(!allowed()||!draft)return;
 const dialog=document.createElement('div');
 Object.assign(dialog.style,{position:'absolute',inset:'48px 0 0',zIndex:'30',background:'#110d16',display:'flex',flexDirection:'column',alignItems:'center',gap:'8px',padding:'8px'});
 const close=document.createElement('button');close.textContent='Închide schița';close.onclick=()=>dialog.remove();
 const caption=document.createElement('span');caption.textContent='Schiță verticală independentă – fără comenzi active';
 const surface=document.createElement('canvas');surface.width=720;surface.height=1280;surface.style.cssText='height:85%;max-width:90%;object-fit:contain;pointer-events:none';
 const ctx=surface.getContext('2d');if(!ctx)return;
 ctx.fillStyle=draft.background;ctx.fillRect(0,0,720,1280);
 for(const e of draft.elements){
  const x=e.x*720/W,y=e.y*1280/H,w=e.w*720/W,h=e.h*1280/H;
  ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();ctx.globalAlpha=e.alpha/100;
  if(!e.transparent){ctx.fillStyle=e.bg;ctx.fillRect(x,y,w,h);}
  if(e.border){ctx.strokeStyle=e.borderColor;ctx.strokeRect(x,y,w,h);}
  ctx.fillStyle=e.color;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=Math.max(10,Math.min(32,h*.35))+'px sans-serif';ctx.fillText(e.label||types[e.type]||e.type,x+w/2,y+h/2,Math.max(1,w-4));ctx.restore();
 }
 dialog.append(close,caption,surface);shell.append(dialog);
 const timer=setInterval(()=>{if(!dialog.isConnected){clearInterval(timer);return;}if(!allowed()){dialog.remove();clearInterval(timer);}},250);
};
$('bfControls').append(portraitButton);
function refreshPages(){""",1)
p.write_text(s)
