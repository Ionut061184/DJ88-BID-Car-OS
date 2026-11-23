# DJ 88 BID Car OS — QF001 / ROCO K706

Launcher Android separat, proiectat pentru 1280 × 720, fără modificarea firmware-ului sau a celor 74 de teme OEM.

## Actualizare funcțională — 23 noiembrie 2026

Codul actual include:
- dată și oră preluate din ceasul dispozitivului;
- vreme prin HTTPS/Open-Meteo, pentru localitatea aleasă manual în bara meteo (Craiova, Robăneștii de Sus, București sau Iași); fără date se afișează indisponibil, nu o temperatură inventată;
- reducere discretă a luminozității interfeței între 20:00–07:00, după ora locală a dispozitivului (nu controlează luminozitatea fizică a ecranului);
- taste media Android anterior / play-pause / următor, transmise către aplicația media care le acceptă; compatibilitatea cu playerul OEM trebuie verificată;
- comenzi Radio / Muzică / DSP / Bluetooth auto prin aplicații OEM exportate sau asocieri explicite;
- butoane pentru Wi-Fi, Bluetooth, setări, listă de aplicații, Google Maps / Waze, YouTube și aplicațiile companion CarPlay / Android Auto dacă sunt instalate;
- informațiile CANBUS necunoscute (tensiune și climatizare) afișate ca **neconectate**. Sunt disponibile doar explicații, nu acțiuni CAN inventate.

## Blocaj de compilare: imaginea aprobată

Fișierul `app/src/main/assets/bid_approved.png` din depozit **nu este încă imaginea finală**, rezultată după corecțiile de culoare și linie laterală aprobate. Workflow-ul include deliberat o verificare strictă SHA-256 care blochează compilarea în această situație. Nu dezactivați controlul pentru a produce din nou un APK cu imaginea greșită.

Pentru următorul APK, fișierul trebuie înlocuit cu imaginea finală, apoi valoarea verificării SHA-256 trebuie actualizată exclusiv după compararea vizuală și confirmarea fișierului real. Ulterior se poate valida un nou build și extrage imaginea din APK pentru comparație.

## Actualizări Android

Flavorul `labSafe` folosește ID `ro.dj88bid.car.labtest`, iar `themesCandidate` folosește `ro.dj88bid.car.qf001theme`. Aceste variante nu sunt actualizări peste orice APK BID vechi. Android cere același applicationId, semnătură și un versionCode crescător pentru un update în loc. GitHub Actions generează APK-uri **debug**, iar semnătura lor nu este garantat persistentă între rulări. Semnarea release stabilă există ca posibilitate Gradle, dar trebuie configurată în CI prin secrete, fără a publica cheia privată.

## Lucruri rămase netestate

- sursa CANBUS / temperatura Climatronic / tensiune baterie;
- starea de redare și titlul real al piesei în widget (lipsă integrare MediaSession verificată);
- seek și mod shuffle/repeat în playerul OEM;
- conectivitatea reală CarPlay/Android Auto prin aplicațiile QF001;
- integrarea directă în Themes original;
- instalarea și comportamentul pe dispozitivul ROCO K706.

Nicio valoare demonstrativă nu trebuie prezentată ca citire reală a mașinii. Păstrați launcherul și Themes originale accesibile.
