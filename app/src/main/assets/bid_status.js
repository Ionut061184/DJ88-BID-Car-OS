/* BID header status: do not substitute simulated weather, battery or connectivity. */
(function(){
 'use strict';
 var weather=document.getElementById('bidWeatherText');
 var bt=document.getElementById('bidBtText');
 var wifi=document.getElementById('bidWifiText');
 var battery=document.getElementById('bidBatteryText');
 var voltage=document.getElementById('bidVoltageText');
 if(!weather||!bt||!wifi||!battery||!voltage)return;
 weather.textContent='—° Craiova';
 // Left: Bluetooth symbol. Right: wireless (Wi-Fi waves) symbol.
 var bluetoothIcon='<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true"><path d="M11 2 L18 8 L13 12 L18 16 L11 22 V2 M5 6 L17 18 M5 18 L17 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
 var wirelessIcon='<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true"><path d="M2 9 Q12 0 22 9 M5 13 Q12 7 19 13 M9 17 Q12 14 15 17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="20" r="1.6" fill="currentColor"/></svg>';
 bt.innerHTML=bluetoothIcon;wifi.innerHTML=wirelessIcon;
 bt.title='Bluetooth: stare necunoscută';wifi.title='Wi-Fi: stare necunoscută';
 bt.style.opacity='.45';wifi.style.opacity='.45';
 battery.textContent='—%';voltage.textContent='— V';
 var oldWeather=window.updateWeather;
 window.updateWeather=function(city,temperature,description){
   if(typeof oldWeather==='function')oldWeather(city,temperature,description);
   var c=typeof city==='string'?city.trim():'';
   var t=(typeof temperature==='number'&&Number.isFinite(temperature))?Math.round(temperature)+'°':'—°';
   weather.textContent=t+(c?' · '+c:'');
   weather.title=description||'';
 };
 function refresh(){
   // Preserve verified QF001 voltage reading (sys.qf.update_battery_power).
   try{
     if(window.BID&&typeof BID.vehicleVoltageSnapshot==='function'){
       var v=JSON.parse(BID.vehicleVoltageSnapshot());
       voltage.textContent=v.available===true&&typeof v.volts==='number'&&Number.isFinite(v.volts)&&v.volts>=9&&v.volts<=16.5?v.volts.toFixed(1)+' V':'— V';
     }else voltage.textContent='— V';
   }catch(_){voltage.textContent='— V';}
   try{
     if(window.BID&&typeof BID.batterySnapshot==='function'){
       var data=JSON.parse(BID.batterySnapshot());
       battery.textContent=Number.isInteger(data.percent)&&data.percent>=0&&data.percent<=100?
         '▣ '+data.percent+'%':'—%';
     }else battery.textContent='—%';
   }catch(_){battery.textContent='—%';}
   try{
     if(window.BID&&typeof BID.connectivitySnapshot==='function'){
       var s=JSON.parse(BID.connectivitySnapshot());
       bt.innerHTML=bluetoothIcon;
       wifi.innerHTML=wirelessIcon;
       bt.style.opacity=s.bluetooth===true?'1':s.bluetooth===false?'.28':'.55';
       wifi.style.opacity=s.wifi===true?'1':s.wifi===false?'.28':'.55';
       bt.setAttribute('aria-label',s.bluetooth===true?'Bluetooth pornit':s.bluetooth===false?'Bluetooth oprit':'Bluetooth indisponibil');
       wifi.setAttribute('aria-label',s.wifi===true?'Wi-Fi pornit':s.wifi===false?'Wi-Fi oprit':'Wi-Fi indisponibil');
     }else{bt.style.opacity='.55';wifi.style.opacity='.55';}
   }catch(_){bt.style.opacity='.55';wifi.style.opacity='.55';}
 }
 // Approved image is contain-fitted: 1536x1024 artwork -> 1080x720,
 // centered horizontally with 100 px side padding. Remap existing touches,
 // without modifying launcher behavior or the underlying screenshot.
 document.querySelectorAll('#stage .hit').forEach(function(button){
   if(button.dataset.bidFitted==='1')return;
   var x=parseFloat(button.style.left);
   var w=parseFloat(button.style.width);
   if(!Number.isFinite(x)||!Number.isFinite(w))return;
   button.style.left=(100+0.84375*x)+'px';
   button.style.width=(0.84375*w)+'px';
   button.dataset.bidFitted='1';
 });
 refresh();setInterval(refresh,15000);
})();
