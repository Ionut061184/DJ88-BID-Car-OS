# DJ 88 BID K706 — auditul v12 al partițiilor dinamice (21.11.2026)

Am verificat **direct** cele 31 de intrări din firmware-ul original `update.zip` (2.433.335.709 B), în special `dynamic_partitions_op_list` și `META-INF/com/google/android/updater-script`, și am comparat cu imaginea PRODUCT modificată v8.

## Dimensiuni confirmate

| Componentă | Octeți |
|---|---:|
| Grup `group_unisoc` maxim | 4.299.161.600 |
| `product` | 1.159.901.184 |
| `vendor` | 312.819.712 |
| `system` | 2.772.692.992 |
| Total alocat | 4.245.413.888 |
| **Nealocat în grup** | **53.747.712** |

Dimensiunea imaginii v8 coincide octet-cu-octet cu alocarea `product` din OTA. În *sistemul de fișiere ext4* v8 rămân doar aproximativ 1.114.112 B liberi; acesta este un indicator **diferit** de spațiul nealocat din grupul de partiții.

## Risc confirmat de script

`dynamic_partitions_op_list` execută `remove_all_groups` și recreează grupul și partițiile `product`, `vendor`, `system`. Scriptul OTA rescrie și `uboot`, `uboot_bak`, `boot`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor`, `dtbo`, `trustos`, `trustos_bak`, `teecfg`, `teecfg_bak` etc. Garda `ro.qf.platform=7862` este insuficientă pentru certificarea unității fizice, a displayului, a MCU și a semnăturii OEM.

## Acțiune efectuată

- Am creat un script Python **numai pentru citire** `audit_dynamic_partitions_v12.py` și un raport JSON din firmware-ul real.
- Patru teste noi au trecut; arhiva de livrare a trecut testul ZIP.
- Nu s-a extins/repartiționat `product`, nu s-au modificat imaginile v7/v8 și nu s-a executat niciun flash.
- `e2fsck` lipsește în acest mediu, iar instalarea apt nu a reușit; testul complet ext4 este **neexecutat**.

## Concluzie

Spațiul nealocat în grup ar putea permite, în principiu, o alocare `product` mai mare, dar **nu o facem încă**: ar necesita reconstruirea coerentă a partițiilor dinamice și a pachetului OTA și o semnătură compatibilă, plus verificarea configurației hardware reale. **v12 este numai un audit offline, nu un firmware de recuperare și nu repară bootloop-ul.**

Livrabil: `DJ88-BID-K706-AUDIT-PARTITII-v12.zip` — cod, raport, teste și README.
