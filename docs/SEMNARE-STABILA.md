# Semnare permanentă pentru DJ 88 BID

## De ce există două tipuri de APK
- **Debug**: se compilează automat pentru teste pe Huawei. GitHub poate folosi alt certificat la fiecare server.
- **Stable signed**: se compilează doar manual, după configurarea unei **chei private permanente**. Pentru actualizări, versiunea instalată trebuie să fie semnată cu același certificat și noua versiune să aibă un `versionCode` mai mare.

**Important:** O aplicație debug existentă, semnată cu alt certificat, **nu poate fi actualizată direct** cu APK-ul stabil. Nu dezinstala aplicația veche fără a salva mai întâi asocierile; dezinstalarea șterge datele aplicației.

## Cum se pregătește cheia (pe un computer de încredere, cu JDK)
1. Generează o singură dată un keystore privat (alege parole lungi, păstrate în siguranță). Exemplu pentru terminal, cu parolă introdusă interactiv:
   ```bash
   keytool -genkeypair -v -keystore bid-release.jks -alias dj88bid -keyalg RSA -keysize 3072 -validity 10000
   ```
2. Păstrează o copie **offline** a fișierului `bid-release.jks` și parolele. Fără această cheie, actualizările semnate cu același certificat nu vor mai putea fi produse.
3. Convertește conținutul în Base64 fără linii noi:
   - Linux: `base64 -w0 bid-release.jks`
   - macOS: `base64 < bid-release.jks | tr -d '\\n'`
   - Windows PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("bid-release.jks"))`
4. În **GitHub → DJ88-BID-Car-OS → Settings → Secrets and variables → Actions**, creează:
   - `BID_KEYSTORE_BASE64` — conținutul Base64 al keystore-ului.
   - `BID_KEYSTORE_PASSWORD` — parola keystore-ului.
   - `BID_KEY_ALIAS` — `dj88bid` (sau aliasul ales).
   - `BID_KEY_PASSWORD` — parola cheii private.
5. Deschide **Actions → Build DJ88 BID stable signed APK → Run workflow**. Descărcarea apare la **Artifacts → DJ88-BID-Launcher-stable-signed** numai după SUCCESS.

## Reguli de siguranță
- Nu încărca niciodată fișierul `.jks`, parolele sau Base64-ul în fișiere publice, mesaje ori capturi.
- Semnarea stabilă se aplică **launcherului separat** `ro.dj88bid.car`, nu aplicațiilor originale QF001.
- **Themes original și firmware-ul rămân nemodificate**.
- Semnătura validează sursa APK-ului, dar nu dovedește că radio, DSP sau Bluetooth auto funcționează pe K706.
