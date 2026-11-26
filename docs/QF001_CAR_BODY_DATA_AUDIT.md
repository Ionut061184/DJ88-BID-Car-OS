# QF001 — Informații despre caroserie, audit 26.11.2026

## Dovezi locale
Inventar de firmware furnizat în proiect: qf_firmware_inventory.json.
- /system/priv-app/QF_Canbus/QF_Canbus.apk
- package com.qf.vehicle, version V1.8-250611.1730, shared UID android.uid.system.
- VehicleMainActivity: MAIN/LAUNCHER, exported nespecificat explicit în inventar.
- com.qf.vehicle.service.VehicleService: enabled=true, exported=true, fără permission declarat pe componentă; acțiune com.qf.vehicle.service.ACTION_CAN_SERVICE.
- FragmentContainerActivity: android.intent.action.startFragmentActivity, DEFAULT. Parametrii nu sunt verificați.
- Nu apare un provider pentru com.qf.vehicle în inventar.
Exportarea unui serviciu nu dovedește accesul la metodele Binder; verificările din implementarea serviciului și semnătura pot limita accesul.

## Referințe externe
https://github.com/mason-coks/qf-headunit-notes/blob/main/docs/06-mcu-protocol.md — QF K706, MCU și parser OEM, testat pe alt vehicul (Chevrolet); nu se transferă automat maparea la Škoda.
https://4pda.to/forum/index.php?showtopic=1065343&st=8500 — utilizator raportează temperatură, turație, combustibil și uși în CanMcu.
https://github.com/patriksh/QF001CarAppOverlay — resurse de interfață CarAPP; nu este API de date.

## Corecția verificabilă acum
Păstrează meniul Mașină și adaugă acces separat la aplicația CAN originală prin acțiunea BID.open('canbus') deja implementată. Nu se modifică firmware-ul.
Broadcastul DATA_SHARE din receptorul actual este o ipoteză de integrare, nu dovadă că datele ajung la BID.
Pentru integrarea live trebuie extras QF_Canbus.apk din arhivele originale deja existente în Drive, urmărite VehicleService.onBind, descriptorul Binder, metodele și permisiunile, CarBodyFragment/CarbodyState și producătorul DATA_SHARE; apoi se testează numai metode de citire permise. Nu se ghicesc coduri de tranzacție, nu se trimit cadre CAN, nu se imită UID-ul de sistem.

## Valori observate în fotografiile OEM (nu se introduc în cod)
Viteză, RPM, kilometraj, combustibil, consum instantaneu, tensiune auto, temperatură exterioară, frână parcare, centură, lichid parbriz. Toate necesită sursă și validare separată. Valoarea 14.0 V din antet și 14.2 V din ecranul OEM nu sunt neapărat aceeași măsurătoare. Păstrează datele indisponibile ca atare.

## Pista partajării per pachet (26.11.2026)
Referință tehnică externă: https://github.com/deviloufr-ai/Dashwheel/blob/main/app/src/main/java/com/openauto/dash/CarBox.kt . Proiectul raportează utilizarea Settings.Global cu cheia formată din numele pachetului destinatar și sufixul KeyShareCarbodyState. Nu reutilizăm codul proiectului, care are licență restrictivă. Informația este o ipoteză pentru versiunea OEM a utilizatorului, nu confirmare pe dispozitiv. BID citește acum numai valoarea propriei chei (absent/0/1/necunoscut/inaccesibil), fără scriere, root, permisiuni noi, apel Binder ori modificarea firmware-ului. Chiar și valoarea 1 nu confirmă recepția sau autenticitatea datelor. Orice activare trebuie să folosească o cale OEM/Android autorizată și să fie reversibilă; nu se forțează accesul dacă firmware-ul îl refuză. Testele browser folosesc date fictive exclusiv pentru verificarea UI.
