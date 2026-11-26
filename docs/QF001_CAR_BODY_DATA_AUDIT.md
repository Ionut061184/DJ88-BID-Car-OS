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

## Activare opțională, autorizată și reversibilă
Instrumentul tools/qf_body_share.py utilizează ADB autorizat de proprietar. Nu se acordă WRITE_SECURE_SETTINGS aplicației și nu se solicită root. Se verifică existența aplicației OEM și a pachetului de test BID. Rulați doar cu mașina staționată, pe un dispozitiv identificat explicit în adb devices. Comanda check nu modifică nimic; enable salvează valoarea anterioară într-un fișier local nou înaintea scrierii unei singure chei; restore restabilește starea anterioară pe același dispozitiv. Dacă firmware-ul refuză operația, opriți testul. Nu încercați să ocoliți restricțiile. Citiți din nou starea în BID, apoi verificați efectiv recepția și valorile OEM. Nu lăsați ADB activ inutil. Nu există încă dovadă că această cheie produce mesaje în versiunea QF a utilizatorului. Testele automate simulează exclusiv comenzile ADB, nu mașina.

## Decodare experimentală și protecție contra pachetelor fără date
Referință pentru pozițiile câmpurilor: https://github.com/deviloufr-ai/Dashwheel/blob/main/app/src/main/java/com/openauto/dash/CarBoxData.kt . Implementare BID independentă, fără copiere de cod. Pentru pachetul de 79 octeți deja implementat, candidații de stare folosesc masca 0x10 și 0x08 la octetul 6 (frână și lichid parbriz) și masca 0x08 la octetul 5 (centură). Valoarea 255 este tratată conservator drept necunoscută pentru octeții de stare. Sensul bitului lichidului trebuie confirmat pe QF001, nu se emite avertizare. Pachetele fără niciun octet informativ sunt respinse și valorile retrase. Fără acțiuni asupra mașinii, fără alerte automate și fără modificarea ecranului principal. Temperatură și tensiune nu sunt extrase prin presupuneri din acest pachet. Testele native construiesc cadre sintetice, nu capturi de pe mașină.

## Audit direct OEM build 55446 — corecție esențială
Sursa: QF_Canbus.apk SHA256 11b019e980ab551ac0e150527fcc4e25992d2d8389541dc4c68368e353d97860, extras din update.zip original. Citirea instrucțiunilor classes2.dex confirmă: GlobalSettingUtil.getAllRequestDataPackages (0x1ec7a8) citește Settings.Global KeyAllPackages; getIsShareCarbodyState (0x1ebdf4) separă lista prin virgulă și testează cheia per pachet. VehicleSender.showCarbodyState (0x1c9048) verifică rezultatul și transmite DATA_SHARE prin sendBroadcastAsUser, cu extra_DATA_SHARE; DataPackageUtil.getCarInfoByte (0x1e74cc) alocă 79 octeți și antet 0x2e, 2. Launcherul original QF_Launcher_BlackBlue.apk, classes.dex, DataShareManager.getInstance (0x2a4560), citește și actualizează lista; addCarBodyStateCallBack (0x2a47ec) setează opt-in per pachet. Corecția înlocuiește helperul anterior care modifica numai cheia per pachet. Noul helper păstrează lista existentă, salvează ambele valori, refuză restaurarea care ar suprascrie modificări ulterioare. APK-ul doar citește starea, fără permisiuni suplimentare. Nicio modificare pe dispozitiv nu a fost efectuată. Testele sunt simulate; recepția rămâne de validat fizic. Nu se distribuie firmware OEM în repo.

## Temperatura exterioară — audit direct OEM 55446
QF_Canbus.apk classes2.dex VehicleSender.sendOutsideTemperature (0x1c85b4) construiește Intent com.qf.vehicle.action.TEMP_STRING cu extra_string și folosește Context.sendBroadcast. VehicleSender normalizează unitățile ℃/℉ înainte de trimitere; SystemUI original (StatusBar$10.onReceive 0x36e5c8) ascultă aceeași acțiune. BID primește pasiv acest mesaj, validează unitatea, convertește Fahrenheit și retrage datele după maximum 120 secunde (decizie conservatoare de test, nu cadență OEM demonstrată). Sursa neautentificată rămâne candidat; nu înlocuiește meteo și nu declanșează alerte. Tensiunea barei SystemUI rămâne proprietatea sys.qf.update_battery_power, deja implementată în MainActivity, distinctă de tensiunea din ecranul de caroserie. Nu se confundă datele și nu se presupune că proprietatea este accesibilă sau actuală pe unitate. Testare fizică neefectuată.

## Climatizare și uși — audit direct 55446
QF_Canbus.apk SHA256 11b019e980ab551ac0e150527fcc4e25992d2d8389541dc4c68368e353d97860. classes2.dex: DataPackageUtil.getAirConditionByte 0x1e7250 (21 octeți, antet 46/1, temperaturi la 7/8), getTemp 0x1e7140 (LO=0, HI=255, necunoscut=254, valoare numerică dublată pentru ℃ sau ℉); getDoorInfoByte 0x1e7c80 (3 octeți, antet 46/3, biți 7..2: față stânga/dreapta, spate stânga/dreapta, hayon, capotă), responseDoorInfo 0x1e8b48 confirmă pozițiile. VehicleSender.showBottomAcLayer consultă getIsShareAcState și trimite DATA_SHARE; showDoorWindowLayer 0x1c9504 consultă getIsShareDoorWindow și trimite DATA_SHARE. Cheile per pachet: KeyShareAcState și KeyShareDoorWindow. BID citește starea cheilor, nu le modifică. Helperul anterior activează doar caroseria; opt-in pentru celelalte două funcții rămâne separat. Mesajele de climatizare și uși sunt candidați neautentificați și expiră după 30 s (limită conservatoare, nu ritm de emisie OEM). Nu se afișează grade numerice cu unitate presupusă. Nicio comandă climatizare/uși și niciun overlay automat, ecranul principal păstrat. Testele sunt sintetice; verificarea fizică rămâne necesară.
