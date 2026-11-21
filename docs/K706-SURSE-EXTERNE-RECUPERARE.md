# ROCO K706 / QF001 / UIS7862S — surse externe și decizie tehnică (21.11.2026)

## Configurația fizică a unității — din fotografiile proprietarului
- Software afișat: `QF001.20250530.200511`.
- SoC: UIS7862S, rezoluție: 1280 × 720.
- MCU: `QF05.V02.12.20250419.004121.05`.
- DSP: BU32107; tuner FM: TEF6686 NXP.
- Simptom: Android începe animația și repornește în buclă, apărut după descărcarea bateriei auto.
- Încercări nereușite: RESET, POWER+RESET, întreruperea alimentării, înlocuirea bateriei.
- Fire marcate KEY1 și KEY2 fotografiate, capete izolate; **nu se conectează la masă fără confirmare tehnică**.

## Identificare online specifică
### MCU: potrivire exactă de familie
În indexul dedicat QF001 sunt listate variante MCU `QF05 V02.12` din **19.04.2025** pentru **BU32107 + TEF6686 (NXP) + 004121**. Această combinație coincide cu configurația de pe unitate; nu demonstrează că orice fișier MCU de pe forum este autentic sau sigur. 
Sursă: https://4pda.to/forum/index.php?showtopic=1065343&st=6220

### Metodă KEY2, comunitate
Utilizatorii descriu recuperarea din USB FAT32 cu fișier `update.zip`, declanșată prin combinație KEY2 + RESET. Este o metodă **de forum, nu instrucțiune oficială verificată pentru exemplarul fizic**.
Sursă: https://4pda.to/forum/index.php?showtopic=1065343&st=1080

### Eșecuri documentate
- Un utilizator relatează că un ciclu de recovery KEY2 a flash-uit firmware-ul dar unitatea a rămas la logo, iar apoi recovery a devenit inaccesibil.
  https://4pda.to/forum/index.php?showtopic=1065343&st=10060
- Un alt caz nu a intrat în update după încercări cu mai multe stickuri USB; deci KEY2 nu este un test diagnostic sigur cu rezultat garantat.
  https://4pda.to/forum/index.php?showtopic=1065343&st=9280

### Pachet de service PAC
Indexul QF001 listează `QF001_PAC._4G_K706_ВОССТАНОВЛЕНИЕ` (recovery), distinct de update prin recovery. Nu presupunem că acesta este aplicabil configurației 7862S/MCU/display a proprietarului.
Sursă: https://4pda.to/forum/index.php?showtopic=1065343&st=5980

### Drivere de ecran
Famila QF001 enumeră mai multe drivere display diferite, unele 1280 × 720. Aceeași rezoluție nu certifică compatibilitatea.
Sursă: https://4pda.to/forum/index.php?showtopic=1065343&st=8960

### Videouri explicative, fără validare pentru unitatea de față
- Tutorial comunitar de update QF001/K706: https://www.youtube.com/watch?v=lk8ixxW788M
- Coduri de setări pentru QF001 (neutilizabile în bootloop): https://www.youtube.com/watch?v=GUW9-107rS0

## Comparație cu update.zip încărcat de utilizator
- Arhiva originală reconstruită din 12 volume are `ROCO/K706/K706:10/QP1A.190711.020/55446:user/release-keys`, `ro.qf.platform=7862`.
- Fotografii: versiunea de interfață anterioară `QF001.20250530.200511`, Android afișat 14. Unele versiuni QF001 pot raporta o versiune comercială Android diferită de API-ul real.
- **Neconfirmat:** driverul exact de display, traseul firmware OTA/corect pentru buildul existent, compatibilitatea partițiilor boot, verificarea semnăturii și dacă pachetul disponibil este adecvat reinstalării fără ștergerea datelor.
- Nici pachetul nostru ZIP de integrare BID și nici APK-ul BID nu sunt un update de boot sau o reparație a unității.

## Decizie
**Nu recomand flash imediat** cu `update.zip` deja recuperat, schimbarea MCU, scurtcircuitarea KEY2 ori utilizarea unui pachet PAC necunoscut. Sunt opțiuni de service numai după confirmarea modelului fizic, a firmware-ului compatibil și verificarea tensiunii unității sub sarcină.

Alternativa practică: un atelier de electronice auto trebuie să observe alimentarea reală BATT/ACC/GND pe conector în timpul buclei și, dacă e stabilă, să verifice o cale de diagnostic/recuperare compatibilă, fără a introduce întâi modificări. Cere să se păstreze MCU QF05 BU32107 TEF6686 și datele OEM; nu folosi firmware pentru UIS8581A doar pentru că numele QF001 seamănă.


## Rezultat nou — potrivire exactă software + MCU în comunitate

Sursa QF001 conține un raport al unui utilizator cu **aceeași versiune exactă de software** `QF001.20250530.200511` și același MCU `QF05.V02.12.20250419.004121.05`, CPU `UIS7862S`, DSP `BU32107`, tuner `TEF6686`, dar cu **ecran 1024 × 600**, nu 1280 × 720:
https://4pda.to/forum/index.php?showtopic=1065343&st=8000

**Rezultat:** potrivirea software/MCU este confirmată independent; **nu** este o dovadă că un pachet de actualizare sau un driver de afișaj destinat celuilalt aparat este compatibil cu al nostru.

### Variante firmware online identificate, NU recomandate automat
Indexul comunității enumeră firmware-uri `QF001_7862s/Jitu2_version_horizontal_screen` din 12.06.2025, 20.06.2025, 14.08.2025, 02.09.2025, 25.11.2025, 26.12.2025 și 05.06.2026. Este un **catalog de versiuni**, nu dovada că una dintre ele repară bootloop-ul și nici o certificare a semnăturii:
https://4pda.to/forum/index.php?showtopic=1065343&st=8000

O altă discuție diferențiază explicit `UIS7862S` de `UIS8581A`: fișierele firmware nu sunt interschimbabile. 
https://4pda.to/forum/index.php?showtopic=1065343&st=4840

Procedurile de update cu `QF/auto` față de `update.zip` sunt distincte și apar în discuții; nu se combină și nu sunt teste neinvazive.
https://4pda.to/forum/index.php?showtopic=1065343&st=4340

**Stare:** am identificat o potrivire exactă de versiune QF001 și MCU, un catalog de firmware al aceleiași familii și două căi comunitare de recuperare. Niciuna nu a fost validată până la instalare pe unitatea proprietarului.
