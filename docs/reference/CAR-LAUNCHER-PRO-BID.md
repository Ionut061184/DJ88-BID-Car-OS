# DJ88 BID — registru de referință tehnică
Data: 27 noiembrie 2026. Referință analizată: Car Launcher Pro 5.7.1.07. Analiză statică a fișierului furnizat de utilizator, fără execuție. Proveniența distribuției nu a fost verificată.

## Acoperire verificată
- 3568 intrări ZIP, CRC fără eroare.
- 2 DEX, 6436 clase, 37024 metode declarate, 32641 corpuri scanate; zero erori ale parcurgerii.
- 1546 XML binare indexate; 69 activități, 23 servicii, 15 receptoare, 4 provideri, 39 declarații uses-permission.
- 166 variante de layout în 46 tipuri de elemente, trei familii de teme.
- Bibliotecile native sunt inventariate, nu dezasamblate. Analiza nu certifică toate ramurile sau funcțiile la execuție.
- Arhiva locală DJ88-BID-BIBLIOTECA-REFERINTA-CAR-LAUNCHER.zip include rapoarte, catalog, indexuri și scripturi proprii de inventariere. Nu publicăm APK-ul, codul terț, activele grafice, cheile sau acreditările.

## Reguli BID
MASTER byte-identic, 23 zone tactile, 1280×720 logic, ramele originale, fundal GPS negru și cele șase scene. Păstrează toate funcțiile validate și comportamentul la contact. Straturi independente, opționale. Configurare numai la staționare. Date reale, sursă și prospețime explicite. Mod standard și resetare. Versiuni de test separate. Nu modifica firmware/MCU și nu ocoli autorizările.

## Catalog de funcții și direcții de implementare proprie
| Modul | Cerințe |
|---|---|
| Widget Studio | Poziție X/Y, dimensiuni independente, opacitate, suprapunere, ordine Z, rotație, fonturi, culoare, aliniere, acțiuni la atingere, adăugare/înlocuire/ștergere, profiluri, blocare, undo și resetare. |
| Widgeturi externe | AppWidgetHost, selector, autorizare Android, configurare, actualizare dimensiuni, păstrare ID, dezabonare. Nu confunda cu motorul hărții. |
| Hartă nativă | Google Maps SDK cu cheie proprie și condiții de facturare verificate; OSM opțional. Hartă/satelit, poziție, zoom, direcție, transparență unde motorul permite, atribuire vizibilă; slot dreapta jos. |
| GPS și călătorie | Viteză reală, altitudine, direcție, distanță, timp, staționare, viteză medie/maximă, sateliți când disponibili. Istoric local opțional, fără traseu salvat implicit. |
| CANBUS QF001 | Car Launcher folosește alt protocol; BID validează mai întâi serviciul OEM, versiunea, autorizarea, abonarea și recepția reală prin diagnosticul separat. Numai citire, fără comenzi CAN. Compară fiecare câmp cu OEM. |
| Media | Radio, muzică și Bluetooth OEM, DSP, volum, MediaSession și metadate doar cu permisiuni justificate. YouTube separat. |
| Volan | Identificare comenzi media/voce reale pe QF001 înainte de integrare. |
| Contact/energie | ACC/sleep/resume, autostart opțional, conservarea comportamentului validat și test consum în repaus. |
| Automatizări | Schimbare widgeturi, evenimente Bluetooth/contact, fallback clar; Smart Drive păstrat. |
| Indicatori | Wi-Fi, Bluetooth, SIM, baterie, tensiune OEM dacă accesibilă, temperatură procesor dacă disponibilă; niciun senzor inventat. |
| Aplicații | Aplicații instalate, ordonare, favorite, iconițe și dezinstalare prin Android. |
| Aspect | Teme suplimentare doar în editor, screensaver, ceas, dată, lumină zi/noapte, animații proprii. |
| Meteo | Sursa existentă, actualizare și date vechi marcate. |
| Backup | Export/import local versionat, verificare și rollback; fără chei API sau trasee în backup necriptat. |
| Extensii | Gesturi locale, Tasker opțional; evită permisiunile excesive și funcțiile fără utilitate confirmată. |

## Model propus de widget
id, type, x, y, width, height, opacity, zOrder, rotation, style, source, tapAction, locked, visible, schemaVersion. Coordonate logice 1280x720 sau normalizate; datele live separate de layout. MASTER imuabil. Widgeturile externe necesită uneori reautorizare la restaurare.

## Ordine de lucru
1. Testează diagnosticul CANBUS deja compilat pe QF001, cu OEM deschis/închis. Nu presupune că recepția funcționează.
2. Prototip hartă nativă, verifică compatibilitatea GMS, cheia proprie, transparența și atribuirea.
3. Widget Studio minimal: ceas, viteză, hartă dacă disponibilă; mutare, dimensiune, opacitate, Z, salvare și resetare.
4. Regresie: MASTER, toate 23 zone, GPS absent/prezent, contact, sleep, radio/muzică/BT, aplicații, indicatori, lipsă internet, restart.
5. Extindere incrementală, în funcție de rezultate.

Aceasta este o specificație de referință, nu un inventar de funcții deja implementate. Nu s-a verificat la execuție fiecare opțiune din aplicația terță și nu s-a modificat codul BID în această ramură de documentație.
