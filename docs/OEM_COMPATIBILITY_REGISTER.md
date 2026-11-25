# Registru de compatibilitate OEM — DJ88 BID

Sursă: update.zip original, ROCO/K706/K706 Android 10, build 55446, SDK 29.
Audit 25.11.2026: 119 manifeste APK decodificate din system.img (38 app, 71 priv-app, 10 preloadapp), 1188 declarații de componente, 34 pachete QF_* inclusiv 11 directoare launcher. Nu este un inventar exhaustiv al partițiilor vendor/product/socko sau al comportamentului la rulare.
Referință BID: Update 4 commit 5f7b7441d50b274b0e0b83124203fb8f988ca929; compilarea confirmată, test telefon confirmat, CAN pe QF001 neconfirmat.

## Regula permanentă
Nu înlocuim o funcție originală cu o funcție BID. Păstrăm accesul original și adăugăm funcțiile BID separat. MASTER neschimbat în afara zonelor aprobate. Nicio valoare simulată prezentată drept reală. Nicio modificare automată MCU, firmware, configurație CAN, calibrare sau permisiuni privilegiate. AI Gardian exclus.

| Funcție | Dovadă OEM (pachet / clasă) | BID actual | Acțiune |
|---|---|---|---|
| Radio FM | com.android.fmradio.ext / com.android.fmradio.FmMainActivity | lansare OEM | test QF001 |
| Audio local | com.qf.musicplayer / com.qf.musicplayer.ui.MainActivity | lansare OEM | test USB și media |
| Bluetooth telefon/muzică | com.qf.bluetooth / BluetoothActivity, MusicActivity | asociere / lansare | păstrare ambele; fără acces agendă |
| DSP | com.qf.soundeffect / SoundActivity | lansare + recomandări profil | test hardware |
| Date auto | com.qf.vehicle / VehicleMainActivity, VehicleService | acces OEM + receptor experimental | verificare partajare pe QF001 |
| Cameră spate/față | com.qf.backcar / MainActivity, FrontVdoActivity | marșarier OEM; Vision detectare | păstrare automatism; verificare acces cameră față |
| 360 | com.st.carkit360camera / MainActivity | detectare generică | verificare hardware/activare; acces oficial |
| DVR | com.fvsm.camera / GuideActivity | detectare generică | acces exact și test |
| Zlink | com.zjinnova.zlink | căutare companion | verificare CarPlay/Android Auto separat |
| TPMS | com.syt.tmps / com.tpms.view.TpmsMainActivity | căutare generică | identificare exactă; verificare modul USB |
| OBD | org.prowl.torque (preload) | detectare generică | verificare instalare și adaptor |
| GPS info | com.qf.beidougps / BeidouGpsActivity | căutare generică launcher | verificare activitate VIEW/MAIN |
| Ventilator | com.qf.fancontrol / FanControlActivity (exportat) | fără acces dedicat identificat | acces OEM explicit, fără control direct |
| Taste volan | com.qf.keystudy / KeyStudyActivity | acces generic | verificare fără schimbarea mapării |
| Taste panou | com.qf.panelkeystudy / PanelKeyStudyActivity | fără acces dedicat identificat | verificare prin meniul OEM |
| Fișiere | com.sprd.fileexplorer / FileExploreActivity | căutare generică | asociere exactă |
| Galerie | com.qf.imagebrowser / ImageBrowserActivity | căutare generică | test |
| Video | com.qf.videoplayer / VideoPlaybackMainActivity | căutare generică | test staționar |
| Vreme | com.qf.weather2 / com.qf.weather.MainActivityV2 | acces OEM generic + meteo BID | păstrare ambele |
| Manual | com.qf.manual / ManualActivity | căutare generică | test |
| Setări auto | com.qf.carsettings / CommonSettingsActivity | acces OEM păstrat | test toate submeniurile |
| Pornire navi/DVR/OBD/TPMS/aplicație | com.qf.carsettings / NavigationStartupActivity, DvrStartupActivity, ObdStartupActivity, TpmsStartupActivity, CustomAppStartupActivity (exportate) | fără acces dedicat identificat | inventar și acces prin meniul OEM |
| Luminozitate/afișaj | com.qf.carsettings / FactoryDisplaySettingsActivity, FactoryBacklightSettingsActivity | BID automat separat | comparație mod OEM, faruri, senzor |
| Microfon | com.qf.carsettings / MicSetActivity | fără acces dedicat identificat | verificare OEM |
| Teme/logo | com.qf.carsettings / FactoryLauncherSelectActivity, LogoSettingActivity | acces Themes + ceas BID | păstrare selector OEM |
| Sleep/wake | com.qf.carsettings / FactorySleepWhiteListActivity, FactoryBackgroundWhiteListActivity | neconfirmat pe Update 4 | test ACC; nu modificăm automat listele |
| Actualizare firmware | com.qf.packageupgrade / OTAService; com.sprd.systemupdate | distinct de actualizarea BID | păstrare OEM; nu declanșăm flash |
| Voce | com.txznet.aipal, com.txznet.txz, com.qf.ai.bridge | neintegrat | verificare disponibilitate locală |

Prezența în manifest nu garantează accesul sau compatibilitatea hardware. Exported nedeclarat nu înseamnă automat accesibil; se verifică prin PackageManager și permisiuni pe dispozitiv. Nu deschidem setări de fabrică ascunse și nu trimitem comenzi hardware automat.

## Criterii de acceptare
- Pe telefon: lipsa datelor OEM afișată clar.
- Pe K706 staționar: butonul Mașină și toate funcțiile originale rămân accesibile; CAN comparat cu OEM; test audio, cameră, luminozitate.
- Test ACC/sleep/wake și revenire HOME fără pierderea configurației.
- Orice funcție nouă trebuie să aibă test de regresie și fallback OEM.
- Nu declarăm paritate completă pe baza compilării sau manifestelor.
