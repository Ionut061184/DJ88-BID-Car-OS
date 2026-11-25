# QF001 — contract de integrare indicatori BID
Data: 2026-11-25. Țintă: ROCO K706, QF001.20250612.232411, Android 10/API 29.
## Dovezi OEM
Surse: QF001_K706_AUDIT_COMPLET_STATIC_v4.zip, apk/system_apks.json și apk/product_apks.json; QF001_OEM_CODE_AUDIT.zip, RAPORT.md. Inventar static al firmware-ului utilizatorului, nu test fizic.
- Toate cele 11 launchere com.android.launcher.* din /system/priv-app nu declară READ_PHONE_STATE; declară CALL_PHONE, locație, stare rețea/Wi-Fi. BID nu are nevoie de CALL_PHONE.
- /product/priv-app/SystemUIWithLegacyRecents_Jitu2/SystemUIWithLegacyRecents_Jitu2.apk, com.android.systemui: READ_PRIVILEGED_PHONE_STATE, MODIFY_PHONE_STATE, BLUETOOTH_PRIVILEGED. Nu transferăm aceste drepturi către BID.
- /system/priv-app/QF_Bluetooth/QF_Bluetooth.apk, com.qf.bluetooth: serviciile TechBTService, BtMainService și TestStartBtService sunt declarate exportate. Exportarea nu demonstrează contractul, permisiunile de apel ori accesul la starea reală. Nu invocăm servicii neauditate. DEX launchere: BluetoothActivity și MusicActivity.
- /system/priv-app/QF_Weather2/QF_Weather2.apk, com.qf.weather2: WeatherServiceV2 exportat; protocolul serviciului nu este verificat. Nu preluăm permisiunile OEM.
- Tensiunea: implementarea BID folosește citire read-only getprop sys.qf.update_battery_power, decivolți; dacă indisponibilă, afișează necunoscut.
## Reguli obligatorii pentru actualizări
1. QF001 este ținta; Huawei este doar test preliminar. Fără root, flash sau modificare SystemUI.
2. Păstrează imaginile MASTER octet cu octet și toate comenzile deja funcționale.
3. Nu declara/cere READ_PHONE_STATE, CALL_PHONE, READ_CONTACTS, WRITE_CONTACTS, READ_CALL_LOG, WRITE_CALL_LOG. READ_BASIC_PHONE_STATE este permisiune normală pentru Android 13+, nu soluție pentru API 29.
4. GPS doar în utilizare pentru meteo; Bluetooth runtime numai dacă Android o cere (API 31+). Datele coordonatelor sunt trimise serviciului meteo pentru prognoză; nu se trimite identitatea celulei.
5. Folosește surse publice Android verificate, marchează starea necunoscută dacă OEM nu expune datele; nu confunda adaptorul Bluetooth Android cu modulul QF. RAT dedus din celulă înregistrată nu dovedește tipul efectiv al conexiunii de date sau 5G NSA.
6. Nu folosi servicii/broadcast-uri/proprietăți QF neconfirmate. Pentru integrare exactă este necesară inspecția DEX SystemUI/QF Bluetooth/QF Weather și un test pe dispozitiv.
## Build 12
Commit 04f869479f22a49884b67722270af5bacb752fab, Actions 45650563357: success; artifact 15038844957. APK LabSafe SHA256 af53d810dcd22f05a3755cb06071963fe54ac0c3b6a5968a2155421113be0c9c. CRC ZIP/APK OK, manifest binar verificat fără permisiuni apeluri/contacte, ambele PNG assets identice cu Build 8. Semnătură debug diferită; nu dezinstala MASTER.
## Criterii de acceptare pe QF001 (staționar)
Instalare LabSafe separat. Verifică prima pornire fără dialog apeluri/contacte, GPS și vreme, semnal real cu SIM introdus și fără SIM, Wi-Fi, Bluetooth QF conectat/deconectat, tensiune comparată cu status bar OEM, funcții originale, camera de marșarier și revenire după contact. Nicio verificare hardware nu este încă confirmată pentru acest build.
