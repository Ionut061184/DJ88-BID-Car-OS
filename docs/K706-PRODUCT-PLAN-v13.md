# DJ 88 BID — v13: plan de extindere PRODUCT, fără modificări (21.11.2026)

**Executat:** scriptul `plan_product_v13.py` a recitit `dynamic_partitions_op_list` din arhiva originală `update-original-verified.zip` și a comparat dimensiunea imaginii PRODUCT BID v8. Testele au rulat pe datele extrase și pe exemple generate; **5/5 au trecut**.

- Grup `group_unisoc`: **4.299.161.600 B**.
- PRODUCT: **1.159.901.184 B**; VENDOR: **312.819.712 B**; SYSTEM: **2.772.692.992 B**.
- Spațiu nealocat în grup: **53.747.712 B (~51,26 MiB)**.
- Scenariu de planificare: **+32 MiB** la `product` ar duce la **1.193.455.616 B** și ar lăsa **20.193.280 B (~19,26 MiB)** pentru grup.
- Cu **16 MiB rezervați ipotetic** (nu o cerință certificată OEM), extinderea maximă calculată și aliniată la 4 KiB este **36.970.496 B (~35,26 MiB)**.
- Scenariul +40 MiB nu păstrează acea rezervă.

**Nu s-a făcut** redimensionarea ext4, schimbarea `dynamic_partitions_op_list`, construirea noului OTA, semnarea OEM sau testul pe dispozitiv. `e2fsck` complet rămâne neexecutat. Scriptul este numai pentru citire și respinge dimensiuni neașteptate ale imaginii.

Pachet: `DJ88-BID-K706-PLAN-CAPACITATE-v13.zip` (script, raport JSON, 5 teste automate și README). **Nu se instalează pe navigație**. Aceste calcule nu dovedesc că pachetul OTA resemnat poate fi acceptat de recovery și nu repară bootloop-ul.
