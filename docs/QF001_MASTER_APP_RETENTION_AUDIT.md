# MASTER QF001 55446 — inventar și politică de păstrare APK
Audit realizat direct asupra celor patru partiții reconstruite din update.zip original. 205 fișiere APK (nu 205 aplicații distincte instalate), 205 manifeste binare citite fără erori; 422 fișiere de configurare text consultate pentru referințe explicite la numele pachetelor. 27 intrări APK au pachetul menționat în NotKillAppsBeforeSleep.ini.
 
| Grup provizoriu | APK-uri | Decizie |
|---|---:|---|
| Sistem/OEM | 110 | păstrează |
| Overlay | 45 | păstrează, verifică ținta și dependențele |
| Launchere originale/teme | 11 | păstrează pentru revenire |
| Opționale pentru interfață | 22 | păstrează instalate; ascundere în BID doar dacă se dorește |
| Candidați pentru audit suplimentar | 17 | nu dezactiva și nu elimina |
| Total | 205 | zero eliminări |
 
Inventarul detaliat QF001-inventar-aplicatii-205.csv este livrat separat utilizatorului; conține cale, dimensiune, SHA256, pachet, versiune, UID partajat, componente, permisiuni, biblioteci, providere, receptori boot, lista de repaus, referințe config și țintă overlay. Nu conține APK-uri sau cod OEM redistribuit.
 
Candidați la audit (nu la eliminare automată): SelfRegister, CallFireWall, Dramtest, SprdAutoSlt, TXZTest, Traceur, USCAIEngine, VceDaemon, TXZAIPal, TXZOverseaAdapter, TXZRadio, TXZSmartWakeUp, TXZTrace, iperf3, QF_AiLit_Bridge, QF_Test, LogManager. Unele sunt system UID, pornesc la boot sau apar în lista de repaus; statutul lor necesită verificarea apelurilor între procese, JNI și integrarea hardware. QF_FanControl, OTA, Framework, CANBUS, Bluetooth, BackCar, SystemUI și WebView rămân protejate. Nu se deduce consumul RAM sau curentul din dimensiunea APK.
 
Descoperire 360°: system/system/app/BirdviewHD_ZR/BirdviewHD_ZR.apk, com.st.carkit360camera, android.uid.system, menționat în lista de repaus; Activate_ZR.apk, com.sjs.activatesdk, android.uid.system, de asemenea în listă. Ambele păstrate. Prezența lor nu dovedește hardware 360° instalat sau licență activă. CameraIPControl este distinctă. Următorul audit va verifica manifestul și legăturile OEM, fără lansare forțată sau modificarea activării.
 
Limitări: manifestele și referințele text nu constituie graful complet al dependențelor dinamice. Nu s-au măsurat procese, RAM, curent, boot sau comportamentul pe unitatea fizică. Niciun pachet nu este declarat sigur pentru eliminare. Firmware-ul și codul executabil BID rămân nemodificate în acest pas.
