# Audit OEM QF001 55446 — GPS, TPMS, USB, proiecție telefon, camere

Sursă: manifestele binare din APK-urile extrase din update.zip original.

| APK | Pachet / activitate | SHA256 |
|---|---|---|
| QF_BeidouGpsInfo | com.qf.beidougps / com.qf.beidougps.BeidouGpsActivity (MAIN/VIEW, fără LAUNCHER) | 5c03fba822e80c6d1c36082e87fa071e5452f58017f072db72487e4987dfd399 |
| gpstest | com.chartcross.gpstest / com.chartcross.gpstest.MainActivity | 1d3ec5e63df8a30aecdf9ca85e9fc238622728899ba444cac4eafcaf31a80e50 |
| TPMS | com.syt.tmps / com.tpms.view.TpmsMainActivity (USB_DEVICE_ATTACHED) | d6b633d08d19a69a915929f1afaf9391d2323caf3dd6586de2a424be6b886227 |
| QF_FileExplorer | com.sprd.fileexplorer / com.sprd.fileexplorer.activities.FileExploreActivity | d20c07583bb3477ed8d01ede59f1527a2b93c385c5f0e56b1355aa3bcfb74e43 |
| zlink5 5.5.2 | com.zjinnova.zlink / com.zjinnova.android.zlink.features.main.MainActivity | 261b37577563c6a1b203e8bfa2f8bf6e94a08c27e23472e5213ed1144e884300 |
| QF_BackCar | com.qf.backcar / MainActivity și FrontVdoActivity | a5f9cb1a1ced0ff6b74332ed428c70cb6bff0418bc8ba88e10bdd415ea4e9801 |
| AndroidAutoStub | com.google.android.projection.gearhead, versiune stub | c4f3157b0b8c0c86c404ce1190a13de1efbfceaffcb9679c0735fcf46d9589d6 |

ZLink declară CarPlayActivity, AutoActivity și HiCarActivity cu enabled=false implicit; disponibilitatea la rulare depinde de configurația și activarea OEM. BID nu activează componentele și nu ocolește licențele. Dacă ruta dedicată nu poate fi lansată, utilizatorul este informat și poate deschide pagina principală ZLink. Stub Android Auto nu dovedește funcționarea recepției Android Auto. TPMS este aplicație pentru dispozitiv USB compatibil, nu dovadă de senzori instalați. FileExplorer oferă acces OEM la fișiere, nu acces BID la întregul spațiu de stocare. Camera IP și BackCar nu dovedesc existența sistemului 360°; nu se forțează lansarea camerei și nu se schimbă setări MCU. Tile 360° afișează doar limitarea, fără a promite funcționare.

Corecție suplimentară: validarea JS a temperaturii numerice climatronic folosește [.] în loc de secvența cu backslash dublu. Eșecul CI 45765333932 / job 139724758562 la așteptarea LO / 21.5 confirmă regresia. Testul existent rămâne neschimbat. Design principal și permisiuni păstrate. Testarea fizică rămâne necesară.
