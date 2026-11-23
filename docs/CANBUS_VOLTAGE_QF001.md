# DJ 88 BID — tensiunea bateriei auto (QF001/K706)
Data: 2026-11-23

## Dovada de pe navigația reală
Fotografia utilizatorului din 23 noiembrie 2026, ecranul OEM „informații despre caroserie”, arată **tensiunea bateriei: 14,3 V** (bara de sus aproximativ 14,0 V), turație 828 RPM, temperatura exterior 8°C, kilometraj 378584, viteză 0. **Valorile sunt de moment**, nu trebuie copiate în launcher drept date live.

## Audit firmware QF001
Pachetul original conține aplicația **com.qf.vehicle**. Auditul anterior a inventariat 205 APK-uri și a inspectat manifestele, **nu a decompilat integral** APK-ul CANBUS ori firmware-ul MCU. Nu există încă dovadă a unei interfețe publice/exportate pentru citirea tensiunii. Diferența de semnătură OEM QF vs BID poate împiedica apelarea API-urilor interne.

## Contract de integrare — implementare numai după verificare
- Sursa trebuie să fie MCU/CANBUS OEM care raportează tensiunea vehiculului; nu Android ACTION_BATTERY_CHANGED, nu fotografii, nu valori fixe sau simulări.
- Integrare **read-only**, fără mesaje CAN de comandă, fără root, fără modificări OEM, MCU sau firmware.
- Tip date: voltage_v (număr), sampled_at_monotonic_ms, source_id, validity/status.
- Reject valori NaN/inf, 0 sau implauzibile (ex. în afara 6–18 V) ca invalid; limita este doar filtru UI, nu criteriu de diagnostic electric.
- Actualizare UI doar din date noi; după 5 s fără date afișează „— V / CANBUS indisponibil”.
- Schimbarea launcherului nu trebuie să modifice modulul CANBUS sau configurarea mașinii.

## Ce lipsește pentru citirea reală
1. Inspecție statică a `com.qf.vehicle` și a bibliotecilor/serviciilor implicate pentru broadcast/provider/AIDL exportate, permisiuni și semnături.
2. Probă read-only pe K706 cu consent: diagnosticarea activităților, serviciilor și evenimentelor fără publicarea datelor personale.
3. Confirmarea endpoint-ului pe hardware și teste cu motor oprit/pornit, comparație cu OEM, inclusiv cazul de timeout.

**Stare:** ecranul OEM dovedește existența datelor; *APK-ul BID nu poate încă citi tensiunea direct*. Build #90 verifică doar vizibilitatea aplicației OEM.
