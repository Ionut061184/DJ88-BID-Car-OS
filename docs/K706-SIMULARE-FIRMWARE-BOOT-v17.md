# K706 / QF001 — simulator de instalare firmware și boot v17

## Implementat și verificat
Am extins simulatorul BID v16 cu un **model virtual al instalării OTA** pornind de la valorile extrase direct din `update-original-verified.zip`:
- `pre-device=K706`, `ota-type=BLOCK`, `post-sdk-level=29`, Android 10 declarat în metadata.
- `group_unisoc=4.299.161.600 B`, `product=1.159.901.184 B`, `vendor=312.819.712 B`, `system=2.772.692.992 B`.
- Configurație fizică din fotografii: UIS7862S, MCU `QF05.V02.12.20250419.004121.05`, DSP BU32107, radio TEF6686, 1280×720, versiune UI `QF001.20250530.200511`.

Simulatorul din browser folosește designul Luxury original inclus în HTML și un bridge Android virtual. Poate rula scenarii de:
1. Instalare simulată a OTA original, cu etape de verificare semnătură, platformă, partiții și boot.
2. Respingere simulată a pachetului modificat BID care **nu deține semnătura OEM**.
3. **Blocare de validare** după instalarea virtuală: compatibilitatea hardware/driver ecran/AVB nu este certificată.
4. Pornire reușită DEMO, bootloop sau blocare la siglă (scenarii selectabile, nu rezultate observate pe K706).
5. Teste pentru funcționarea meniurilor și bridge-ului virtual.

## Teste browser executate
Testele Playwright + Chromium headless au trecut efectiv:
- **7/7** verificări de model OTA/configurație.
- Refuzul virtual al OTA BID nesemnat OEM.
- Finalizarea instalării virtuale originale cu mesaj explicit **hardware neconfirmat**.
- Scenariu demo boot reușit către interfața BID.
- Scenariu demo bootloop.
- Fără erori JavaScript raportate de pagina testată.

## Artefacte
- `DJ88-BID-K706-SIMULATOR-FIRMWARE-BOOT-v17.html` (self-contained cu imaginea Luxury originală).
- `DJ88-BID-K706-SIMULATOR-FIRMWARE-BOOT-v17.zip` (HTML + script de test + date de verificare + captură browser).

## Limită esențială
**Nu este emulator al SoC UIS7862S, nu instalează firmware și nu rulează efectiv Android/Linux K706.** Nu dovedește că unitatea fizică poate boota, că driverul ecranului este corect, că MCU/DSP funcționează, că recovery acceptă imaginea modificată sau că bootloop-ul este reparat. Aceste concluzii necesită verificare pe aparatul fizic și o cale de instalare validată. Nu folosi aceste fișiere ca `update.zip`.
