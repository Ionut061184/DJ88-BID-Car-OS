/* BID header status: do not substitute simulated weather, battery or connectivity. */
(function(){
 'use strict';
 var weather=document.getElementById('bidWeatherText');
 var bt=document.getElementById('bidBtText');
 var wifi=document.getElementById('bidWifiText');
 var battery=document.getElementById('bidBatteryText');
 var voltage=document.getElementById('bidVoltageText');
 if(!weather||!bt||!wifi||!battery||!voltage)return;
 var oldWeather=window.updateWeather;
 window.updateWeather=function(city,temperature,description){
   if(typeof oldWeather==='function')oldWeather(city,temperature,description);
   var c=typeof city==='string'?city.trim():'';
   var t=(typeof temperature==='number'&&Number.isFinite(temperature))?Math.round(temperature)+'°':'—';
   weather.textContent=t+(c?' · '+c:'');
   weather.title=description||'';
 };
 function refresh(){
   // Preserve verified QF001 voltage reading (sys.qf.update_battery_power).
   try{
     if(window.BID&&typeof BID.vehicleVoltageSnapshot==='function'){
       var v=JSON.parse(BID.vehicleVoltageSnapshot());
       voltage.textContent=v.available===true&&typeof v.volts==='number'&&Number.isFinite(v.volts)&&v.volts>=9&&v.volts<=16.5?v.volts.toFixed(1)+' V':'';
     }else voltage.textContent='';
   }catch(_){voltage.textContent='';}
   try{
     if(window.BID&&typeof BID.batterySnapshot==='function'){
       var data=JSON.parse(BID.batterySnapshot());
       battery.textContent=Number.isInteger(data.percent)&&data.percent>=0&&data.percent<=100?
         '▣ '+data.percent+'%':'';
     }else battery.textContent='';
   }catch(_){battery.textContent='';}
   try{
     if(window.BID&&typeof BID.connectivitySnapshot==='function'){
       var s=JSON.parse(BID.connectivitySnapshot());
       bt.textContent=s.bluetooth===true?'ᛒ':s.bluetooth===false?'ᛒ̸':'';
       wifi.textContent=s.wifi===true?'◉':s.wifi===false?'◌':'';
       bt.setAttribute('aria-label',s.bluetooth===true?'Bluetooth pornit':s.bluetooth===false?'Bluetooth oprit':'Bluetooth indisponibil');
       wifi.setAttribute('aria-label',s.wifi===true?'Wi-Fi pornit':s.wifi===false?'Wi-Fi oprit':'Wi-Fi indisponibil');
     }else{bt.textContent='';wifi.textContent='';}
   }catch(_){bt.textContent='';wifi.textContent='';}
 }
 refresh();setInterval(refresh,15000);
})();
