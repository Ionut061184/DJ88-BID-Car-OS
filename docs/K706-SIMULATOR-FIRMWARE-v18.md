# K706 DJ 88 BID — simulator v18, inspecție ZIP reală și fault injection

Data: 2026-11-21

## Livrabil implementat
Simulatorul HTML v17 a fost extins la v18. Include interfața originală BID 1280×720, încărcare locală a unui ZIP (fără upload la server), citire central directory, EOCD, lista intrărilor, extragerea metadatelor `pre-device` și `post-sdk-level` când metoda de compresie e suportată, limite de dimensiune, jurnal PASS/FAIL/BLOCKED/UNVERIFIED și export JSON.

**Proba reală:** simulatorul a citit ZIP-ul original reconstruit de **2.433.335.709 B** și a identificat **31** intrări, `pre-device=K706`, `post-sdk-level=29` și componentele critice OTA. Pentru ZIP mare, browserul marchează **BLOCKED** verificarea SHA-256 completă; pentru semnătura PKCS#7 afișează **UNVERIFIED**, chiar dacă un audit offline anterior v15 a confirmat originalul. Un ZIP încărcat nu poate fi selectat drept dovadă de instalabilitate numai fiindcă structura e corectă.

## Scenarii virtuale
- Original QF: scenariu de etape recovery, partiții dinamice, boot. Rezultat final **BLOCKED pentru boot hardware**, nu PASS.
- BID custom fără semnătură OEM: **FAIL / STOP**.
- Defecte injectate: model incompatibil, semnătură invalidă, ZIP corupt, spațiu insuficient, SELinux invalid, mount eșuat, AVB eșuat, power loss și Radio OEM absent.
- Simulare pornire Android și launcher BID păstrată din v17, strict DEMO.
- Export JSON cu evenimente, metadate și marcaje de incertitudine.

## Teste efectiv executate
Playwright + Chromium headless: **9/9 PASS**:
1. Pornire model firmware și limite dynamic partitions.
2. Refuz OTA BID fără semnătură QF.
3. Oprire la dispozitiv incompatibil.
4. Oprire la pierderea alimentării.
5. Original virtual ajunge la stare de boot hardware BLOCKED.
6. ZIP fals/corupt respins.
7. ZIP sintetic recunoscut structural, dar fără aprobare de semnătură.
8. Citirea ZIP original de 2,43 GB (31 intrări; K706; API 29).
9. Blocarea instalării virtuale a ZIP-ului încărcat până la verificare criptografică independentă.

Erori JavaScript în aceste scenarii: **zero**. Arhiva livrabilă ZIP integră.

## Livrabil și reutilizare
- `DJ88-BID-K706-SIMULATOR-FIRMWARE-v18.html` (self-contained).
- `DJ88-BID-K706-SIMULATOR-v18.zip` (HTML, cod build, teste, screenshot, raport).
- Instrumentul de verificare criptografică offline existent `verify_k706_ota.py` din v15 se folosește separat.

## Limite clar delimitate
Acest simulator **nu rulează Android**, **nu emulează SoC UIS7862S**, **nu scrie firmware**, **nu validează semnăturile/AVB runtime din browser**, **nu repară bootloop-ul** și **nu confirmă compatibilitatea MCU QF05 / display**. Ext4 complet cu `e2fsck`, semnare acceptată de OEM și verificare pe unitatea fizică rămân neexecutate.

## Prioritatea următoare
Audit ext4 complet pe copie, validare recuperare fizică în service fără flash de probă, configurarea unei metode legitime de instalare BID după repararea bootloop-ului.
