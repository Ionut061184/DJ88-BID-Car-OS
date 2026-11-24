/* BID header status: do not substitute simulated weather, battery or connectivity. */
(function(){
 'use strict';
 var weather=document.getElementById('bidWeatherText');
 var bt=document.getElementById('bidBtText');
 var wifi=document.getElementById('bidWifiText');
 var battery=document.getElementById('bidBatteryText');
 if(!weather||!bt||!wifi||!battery)return;
 var oldWeather=window.updateWeather;
 window.updateWeather=function(city,temperature,description){
   if(typeof oldWeather==='function')oldWeather(city,temperature,description);
   var c=typeof city==='string'?city.trim():'';
   var t=(typeof temperature==='number'&&Number.isFinite(temperature))?Math.round(temperature)+'°':'—';
   weather.textContent=t+(c?' · '+c:'');
   weather.title=description||'';
 };
 function refresh(){
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
