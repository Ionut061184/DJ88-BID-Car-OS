# DJ 88 BID — audit ext4 aprofundat v10 (21.11.2026)

**Audit real executat, numai pentru citire** pe cele două imagini ext4 existente:
- `DJ88-BID-K706-PRODUCT-INTEGRAT-v7.img`
- `DJ88-BID-K706-PRODUCT-SELINUX-v8.img`

Instrument: cod C compilat cu `libext2fs`; recitește bitmapurile, inodurile alocate, directoarele și blocurile de date obișnuite. Inodurile ext4 speciale (1–10) nu sunt interpretate ca fișiere obișnuite; referințele și contoarele acestea necesită regulile dedicate dintr-un fsck complet.

## Rezultate v8
- 630 inoduri alocate; 454 fișiere normale, 167 directoare, 1 symlink, 8 inoduri speciale.
- 0 erori citire inoduri; 0 erori de tip director; 0 erori iterator bloc.
- 0 referințe de bloc nealocat sau în afara imaginii în scanarea efectuată; 0 dubluri de bloc în referințele scanate.
- **272 blocuri libere × 4096 B = 1.114.112 B**; 90 inoduri libere. Aceeași statistică și pentru v7.
- SHA-256 v8: `b98827b4db68b606c36b2706480fce551ca944154235e64c265baa0f790edd06`.
- SHA-256 APK: `cb3b4c7e8e599804e2ddbd92ead0143c88e57605ae8f1d99a2f1d030a995862f`.
- Testele pachetului v10 (4) au trecut; ZIP testat.

## Interpretare și limitări
**Acesta NU este un `e2fsck` complet**, care nu era disponibil în mediu. Auditul aprofundat nu garantează consistența tuturor structurilor ext4, securitatea SELinux la runtime, semnătura OEM, compatibilitatea display/MCU și recuperarea bootloopului. Nu s-a extins partiția (fără tabel de partiții și verificarea dimensiunilor din dynamic partitions) și nu s-au șters aplicațiile OEM.

**Fișierul v8 NU este OTA și NU se flash-uiește.** Pachetul `DJ88-BID-K706-AUDIT-APROFUNDAT-v10.zip` conține codul auditului, rapoarte JSON, APK verificat, README și teste, dar nu include imaginea de 1,16 GB.

## Următoarea verificare
Un `e2fsck -fn` pe copia imaginii, urmat de analiza capacității `product` în raport cu dynamic partitions; în paralel, o cale verificată de recuperare bootloop pentru buildul QF001.20250530.200511. Nu se fac flash-uri de probă și nu se scurtcircuitează KEY2.
