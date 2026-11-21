# QF001 K706 — identificare OEM verificată din update.zip (21.11.2026)

## Proveniența
- 12 volume `update.part01.rar` … `update.part12.rar` recuperate prin linkuri Drive furnizate de proprietar.
- Arhiva multipart RAR5 verificată și extrasă complet ca `update.zip`, **2.433.335.709 octeți**.
- `META-INF/com/android/metadata`: `ROCO/K706/K706:10/QP1A.190711.020/55446:user/release-keys`, Android 10, build 55446.
- Partiția `system` reconstruită din `system.new.dat.br` și `system.transfer.list`; partiția `product` reconstruită similar.
- Fișierele `.apk` au fost citite **fără instalare sau modificare** din imaginea ext originală. Manifestele Android binare au fost analizate offline.
- Inventar: 120 de APK-uri pe `system`; 80 pe `product`. Numărul include aplicații Android generale, aplicații OEM și overlay-uri.

## Componente identificate direct

| Funcție | APK din system/priv-app | Pachet Android | Activitate cu intent MAIN/LAUNCHER din manifest |
|---|---|---|---|
| Radio FM | `QF_FMRadioExt/QF_FMRadioExt.apk` | `com.android.fmradio.ext` | `com.android.fmradio.FmMainActivity` |
| Bluetooth auto | `QF_Bluetooth/QF_Bluetooth.apk` | `com.qf.bluetooth` | `com.qf.bluetooth.BluetoothActivity` |
| Bluetooth muzică | același APK | `com.qf.bluetooth` | `com.qf.bluetooth.MusicActivity` |
| DSP / egalizator | `QF_DSP/QF_DSP.apk` | `com.qf.soundeffect` | `com.qf.soundeffect.SoundActivity` |
| Muzică | `QF_MusicPlayer/QF_MusicPlayer.apk` | `com.qf.musicplayer` | `com.qf.musicplayer.ui.MainActivity` |
| Setări auto | `QF_CarSettings/QF_CarSettings.apk` | `com.qf.carsettings` | `com.qf.carsettings.activity.CommonSettingsActivity` |
| CANBUS | `QF_Canbus/QF_Canbus.apk` | `com.qf.vehicle` | `com.qf.vehicle.activities.VehicleMainActivity` |

**Ce demonstrează tabelul:** pachetele și numele activităților sunt prezente în manifestele APK-urilor originale. Intențiile MAIN/LAUNCHER sunt declarate. **Nu demonstrează** că pornirea dintr-un APK separat, fără semnătură OEM, este permisă pe K706 sau că funcțiile hardware vor merge în starea actuală de bootloop.

## Alte observații
- APK-ul `TXZRadio` există și în `/system/preloadapp/`, separat de aplicația FM.
- `QF_Canbus` conține clasele `OriginalTuner` și `OriginalMediaPlayer`, dar acestea nu sunt scurtături generale recomandate pentru DJ 88 BID.
- APK-urile originale includ servicii și acțiuni interne. Nu se presupune că sunt publice sau sigure pentru apeluri dintr-un launcher obișnuit.
- Themes original, imaginea de sistem și bootloaderul **nu au fost modificate**.

## Verificări înainte de utilizare
1. Aplicația DJ 88 BID testează existența componentelor OEM prin PackageManager, dar nu le execută automat.
2. Pe K706 funcțional, utilizatorul poate asocia manual o aplicație disponibilă pentru fiecare funcție.
3. Când K706 revine din bootloop, testarea trebuie făcută fără înlocuirea launcherelor privilegiate și fără flash.
