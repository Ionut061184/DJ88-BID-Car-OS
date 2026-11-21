# DJ 88 BID Car OS

Launcher Android separat pentru navigația QF001/K706, afișaj 1280 × 720.

## Stadiul real (21 noiembrie 2026)

Sunt încărcate configurația Gradle, manifestul Android, `MainActivity.kt`, interfața `index.html` și fluxul GitHub Actions pentru compilarea `app-debug.apk`.

**Lipsește încă imaginea originală aprobată:** `app/src/main/assets/bid_approved.png`. Workflow-ul oprește intenționat compilarea până când este adăugată, pentru a nu produce un APK cu ecranul BID gol. Imaginea a fost verificată local la 1280×720.

### Încărcarea imaginii

În GitHub: Add file → Upload files și încărcați `bid_approved.png` în directorul `app/src/main/assets/`. După aceea, deschideți Actions → Build DJ88 BID Android APK → Run workflow. APK-ul apare la **Artifacts** după o compilare reușită.

### Ce este implementat în sursele actuale

Interfața Luxury cu zone tactile, mod Driving demonstrativ, aplicații Android (Maps, Waze, YouTube), telefon, Bluetooth, setări, lista aplicațiilor, comanda de revenire la selectorul de launcher și un diagnostic de bază.

**Nu sunt încă implementate sau testate complet:** harta live în panoul ilustrativ, zoom/centrare în panoul desenat, vremea reală, tensiunea auto, radio/DSP și integrarea directă în aplicația Themes. Nici compilarea finală, nici testele pe K706 nu sunt confirmate.

## Siguranță

Themes original, celelalte launchere și firmware-ul QF001 **rămân nemodificate**. Proiectul nu este un firmware. Nu se înlocuiește un APK de sistem semnat de producător cu această versiune independentă.
