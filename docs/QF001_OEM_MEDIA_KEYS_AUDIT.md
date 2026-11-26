# Audit direct OEM multimedia și comenzi — build QF001 55446

Sursa: AndroidManifest.xml binar din APK-urile originale extrase din update.zip al utilizatorului. Nu sunt APK-uri descărcate de pe internet. Toate componentele de mai jos sunt din system/system/priv-app.

| APK | Pachet / activitate | SHA256 |
|---|---|---|
| QF_FMRadioExt | com.android.fmradio.ext / com.android.fmradio.FmMainActivity | 46c451a8906bf78de7347e5a3d974c19c37b400892c1f838032d5cdb6687c941 |
| QF_DSP | com.qf.soundeffect / com.qf.soundeffect.SoundActivity | 7fc2f8265ab299cb229bdc727dae724fda21d276f5a896ecf2e67f16da0ffdea |
| QF_Bluetooth | com.qf.bluetooth / com.qf.bluetooth.BluetoothActivity și com.qf.bluetooth.MusicActivity | 8c800aa4ef24158274153b2cc7d14b31ee4237e7d21d5b383479a458a9af4a28 |
| QF_MusicPlayer | com.qf.musicplayer / com.qf.musicplayer.ui.MainActivity | ba78a5d76eeb3951a6ccca852adcc39891ee3177fbb9596a33f271c7e4f33168 |
| QF_KeyStudy | com.qf.keystudy / com.qf.keystudy.ui.KeyStudyActivity | 1c65395ddb93590901e31ebf0aed06e66ede4643bc508e6cdbd6a910024488d3 |
| QF_PanelKeyStudy | com.qf.panelkeystudy / com.qf.panelkeystudy.ui.PanelKeyStudyActivity | df60e254edefecf82406f255ef99aff35df06e26ae38b6673ca12974d4327433 |

BluetoothActivity și MusicActivity au ambele MAIN/LAUNCHER; MusicActivity declară exported=true. DSP și MusicPlayer declară exported=true. KeyStudy și PanelKeyStudy nu declară explicit exported; PanelKeyStudy are MAIN/VIEW fără categoria LAUNCHER în manifestul inspectat. Disponibilitatea reală se decide prin PackageManager și permisiuni pe unitate, nu prin presupunere. Nu se forțează activități private. Toate APK-urile declară android.uid.system; BID nu imită UID-ul și nu copiază APK-uri în distribuție.

QF_Framework.apk classes.dex: com.qf.framework.utils.KeyUtils.sendInputEvent (0x6066c, 0x606e4) construiește KeyEvent și invocă InputManager.injectInputEvent. Aceasta confirmă calea OEM, nu maparea tuturor butoanelor pe mașina utilizatorului. BID păstrează mecanismul OEM; nu interceptează, injectează sau remapează butoanele fizice. Accesul la configurarea volanului/panoului se face numai la cererea utilizatorului, prin activitatea OEM dacă este accesibilă.

Corecție BID: două rute distincte telefon și muzică BT; prioritate componentei exacte, verificarea exported/enabled/permission, fără fallback ambiguu la același pachet Bluetooth. Radio/DSP/player păstrează lansările OEM existente. Comenzi volan și panou separate în sertarul Funcții, fără modificarea ecranului principal. Testele de contract verifică codul și manifestul, nu dispozitivul. Hardware și accesul efectiv la configurare rămân neconfirmate.
