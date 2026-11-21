# Analiză offline QF001 — situația verificată (21.11.2026)

## Sursa și limita acestei note
Raportul original `Raport_Themes_QF001_DJ88BID.txt` descrie reconstrucția imaginii Android QF001 din opt volume `system.new.dat.part*.rar` aflate în Google Drive. Această notă este o transcriere structurată a rezultatelor raportului, nu o nouă extragere a fișierelor binare.

## Constatări reale
- Arhiva multipart a fost refăcută ca `system.new.dat.br` (1.626.743.585 octeți).
- Imaginea `system.img` (2.768.625.664 octeți, format ext) a fost reconstruită.
- `/system/config/custom_launcher/launcher_config.cfg` conține 74 de intrări în format `pachet#activitate#preview#wallpaper`.
- În `/system/config/custom_launcher/` sunt previzualizări `launcher_style_*` și fundaluri `default_wallpaper_*`.
- În `/system/priv-app/QF_Launcher_*/` sunt instalate APK-urile OEM.

Exemple confirmate în raport:
```text
com.android.launcher.audi#com.android.launcher3.Launcher#launcher_style_audi.jpg#default_wallpaper_audi.png
com.android.launcher.gradient.black#com.android.launcher3.Launcher#launcher_style_gradient_black.jpg#default_wallpaper_gradient_black.png
com.android.launcher.swood.grain#com.android.launcher3.Launcher#launcher_style_swood_grain.jpg#default_wallpaper_swood_grain.png
```

- `QF_Launcher_BlackBlue.apk`: 12.033.255 octeți, 1.264 intrări ZIP.
- `QF_Launcher_SwoodGrain.apk`: 13.292.586 octeți, 1.290 intrări ZIP.

## Ce NU este încă verificat
- Pachetul și activitatea Android originale pentru **Radio, Muzică, Bluetooth auto și DSP**; nu apar identificate în raport.
- Modul exact prin care aplicația OEM Themes selectează/activează launcherele.
- Compatibilitatea directă a launcherului separat `ro.dj88bid.car` cu serviciile privilegiate OEM.
- Recuperarea unității K706 care nu mai pornește.

## Decizie practică
1. Păstrăm firmware-ul și Themes OEM nemodificate.
2. Folosim Huawei pentru testele de UI ale DJ 88 BID.
3. Nu punem pachete Android inventate în Radio/DSP/BT.
4. Când avem APK-urile originale ale funcțiilor (nu doar ale launcherelor), analizăm manifestele **offline**, apoi implementăm doar lansări publice, verificate.
5. Nu flash-uim o imagine de sistem refăcută sau nesemnată pentru a testa un launcher.

Această notă nu dovedește că modul de recuperare K706 funcționează.
