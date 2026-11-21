# K706 PRODUCT v14 — comparație completă a intrărilor originale (21.11.2026)

## Execuție pe imagini reale, exclusiv read-only
Am compilat `manifest.c` cu libext2fs și OpenSSL, am parcurs recursiv ext4:
- original: `product-original.img` (**619 intrări**);
- personalizat: `DJ88-BID-K706-PRODUCT-SELINUX-v8.img` (**621 intrări**).

Pentru fiecare intrare am comparat calea, tipul, permisiunile, UID/GID și eticheta `security.selinux`; pentru fișierele obișnuite am citit integral conținutul și am calculat SHA-256.

### Rezultat
- **0 intrări OEM eliminate.**
- **0 modificări** în câmpurile auditate ale celor 619 intrări originale.
- Exact două intrări noi:
  - `/app/DJ88BID`, mod 0755, UID:GID root:root, etichetă SELinux `u:object_r:system_file:s0`;
  - `/app/DJ88BID/DJ88-BID.apk`, mod 0644, UID:GID root:root, aceeași etichetă, SHA-256 `cb3b4c7e8e599804e2ddbd92ead0143c88e57605ae8f1d99a2f1d030a995862f`.
- 6 teste automate ale comparatorului au trecut (adăugare corectă; fișier OEM modificat; fișier OEM lipsă; adăugare neașteptată; etichetă SELinux greșită; APK incorect).
- Testul ZIP al arhivei v14 a trecut.

## Livrabil
`DJ88-BID-K706-COMPARATIE-OEM-v14.zip`: cod C pentru parcurgere ext4, comparator/teste Python, manifeste, raport JSON, jurnal teste și instrucțiuni.

## Ce NU certifică
Comparația nu acoperă toate metadatele ext4 sau un `e2fsck` complet. Nu dovedește funcționarea Android pe K706, compatibilitatea firmware-ului cu ecranul/MCU, acceptarea prin recovery ori validitatea semnăturii OEM. **Nu este un pachet de instalare. Bootloop-ul nu este reparat.**

## Următorul blocaj
Necesare: verificare ext4 prin `e2fsck`, test pe copie cu redimensionare controlată, plus un lanț legitim de semnare/recuperare. Nu flash-uim imaginile offline pe dispozitiv înainte de verificarea compatibilității și semnăturilor.
