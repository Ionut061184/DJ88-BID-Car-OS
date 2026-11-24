# DJ88 BID — compatibilitate cu tema originală QF001

Stare: 24 noiembrie 2026. Acesta este un contract tehnic pentru dezvoltare, **nu o confirmare de compatibilitate pe unitatea fizică**.

## Ce a arătat auditul firmware-ului OEM ROCO K706/QF001

- Android 10; firmware-ul analizat are identificatorul `QF001.20250612.232411`.
- `/system/config/custom_launcher/launcher_config.cfg` conține **74 de intrări de launcher** în format `package#activity#preview#wallpaper`.
- Launcherele originale includ APK-uri separate `QF_Launcher_*` în `/system/priv-app`; selectorul de teme nu schimbă doar o imagine.
- `QF_CarSettings.apk` conține `FactoryLauncherSelectActivity`, iar logica OEM menționează proprietăți de sistem și repornire.
- Un APK BID instalat obișnuit **nu este automat inclus în catalogul Themes**; compatibilitatea cu sistemul de semnare și permisiunile originale nu este confirmată.

Bază: rapoartele locale `Raport_Themes_QF001_DJ88BID.txt` și `QF001_VERIFICARE_SELECTOR_SEMNATURI_2026-11-21.txt`, produse din analiza statică a firmware-ului. Nu sunt teste executate pe unitatea QF001.

## Cele două variante BID existente

| Variantă | Pachet | Rol |
| --- | --- | --- |
| `labSafe` | `ro.dj88bid.car.labtest` | Deschidere manuală; **nu se declară HOME**. |
| `themesCandidate` | `ro.dj88bid.car.qf001theme` | Declară o activitate HOME de test; **nu garantează apariția în Themes OEM**. |

Niciuna nu trebuie instalată ca aplicație de sistem, nici să suprascrie launcherele OEM existente. Nu se modifică OTA, firmware-ul de boot, MCU, CANBUS sau componentele de siguranță.

## Funcții de păstrat și de verificat

- Ecranul BID aprobat la **1280 × 720** rămâne imuabil vizual. Ultimul PNG efectiv folosit de APK-ul de telefon (`assets/bid_fullbleed.png`) are SHA-256 `fbebff471162177ce8df8c7e7f157b29692e2750d3b3b3ba9f8a0eb3139bfc2b`. **Acest PNG final este deja prezent, byte-for-byte, în ramura GitHub** la `app/src/main/assets/bid_fullbleed.png`; buildul a fost corectat să **nu îl regenereze** și să verifice SHA-256 atât în sursă, cât și în APK. Nu confunda această verificare cu confirmarea funcțiilor QF001 pe hardware.
- Ultima corecție a benzii meteo/Bluetooth/Wi-Fi este `#bidStatusLive{left:837px;}` și **a fost sincronizată în sursa GitHub**; ultima poziționare a orei/datei este de asemenea sincronizată (`#stage:after` la `left:140px`, ceas `left:160px`, dată `left:345px`). Testele de regresie verifică aceste coordonate.
- Butonul **Muzică** încearcă `com.qf.musicplayer`, nu YouTube. YouTube rămâne separat.
- Meniul **Aplicații** folosește lansatoarele detectate din Android la deschidere, cu paginare 5 × 2, ordine persistentă și apăsare lungă. Tragerea în coș apelează dialogul de dezinstalare Android, **niciodată dezinstalare silențioasă**.
- Radio, Bluetooth auto, DSP și setările auto pot porni numai activități publice/exportate ori asociate explicit; absența lor este afișată ca atare, nu simulată.
- Camera de marșarier și funcțiile critice CANBUS rămân controlate de sistemul original. Nu se simulează sau se interceptează marșarierul.
- Selectorul Themes OEM se deschide doar dacă activitatea este exportată și Android permite lansarea.
- Informațiile despre vreme, baterie, conectivitate și tensiune nu trebuie inventate dacă nu sunt disponibile.

## Teste și acceptanță

1. Rulare automată `python3 -m unittest discover -s tests -p 'test_*.py' -v`, inclusiv `test_qf001_themes_contract.py`.
2. APK-ul `labSafe` pornește manual, fără a apărea ca HOME; nu schimbă imaginea BID și nu afectează tema originală.
3. Pe QF001 funcțional: verificăm separat Radio, Music, Bluetooth, DSP, Apps, Waze/YouTube și comportamentul de instalare/dezinstalare. Captura de pe Huawei **nu confirmă** aceste funcții pe aparat.
4. `themesCandidate` se încearcă **numai după** confirmarea mecanismului și a posibilității de revenire la launcherul OEM. Nu se setează automat ca HOME.
5. În cazul în care QF001 pornește în buclă (bootloop), recuperarea aparatului se tratează separat, fără flash experimental pentru a instala BID.

## Următorul pas tehnic pentru integrarea completă

PNG-ul final și coordonatele ultimului antet au fost sincronizate în GitHub și sunt protejate de testele de regresie. Urmează verificarea instalării **labSafe** pe unitatea reală QF001 și a tuturor zonelor tactile; numai după aceea se analizează acceptarea unei variante HOME/selector Themes. Un APK semnat cu cheia de test nu dobândește permisiunile unui APK OEM prin redenumire.
