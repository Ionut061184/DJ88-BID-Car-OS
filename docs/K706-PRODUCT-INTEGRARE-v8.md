# ROCO K706 — DJ 88 BID PRODUCT v8: etichete SELinux (21.11.2026)

## Problema verificată
În imaginea ext4 `product` construită la v7, dosarul `app/DJ88BID` și `app/DJ88BID/DJ88-BID.apk` aveau modurile corecte (0755, respectiv 0644), proprietar root:root, dar **lipsea atributul ext4 `security.selinux`**. Aplicațiile OEM din această imagine au `u:object_r:system_file:s0`, inclusiv `app/Chrome`.

## Remediere executată
Pe **o copie** a imaginii v7, biblioteca `libext2fs` a setat atributul `security.selinux=u:object_r:system_file:s0` pe ambele intrări. După scriere, am deschis din nou imaginea numai pentru citire și am validat:
- `app/DJ88BID`: root:root, 0755, `u:object_r:system_file:s0`
- `app/DJ88BID/DJ88-BID.apk`: root:root, 0644, `u:object_r:system_file:s0`
- APK extras identic cu APK-ul original (SHA-256 `cb3b4c7e8e599804e2ddbd92ead0143c88e57605ae8f1d99a2f1d030a995862f`)
- Imagine v8: `DJ88-BID-K706-PRODUCT-SELINUX-v8.img`, 1.159.901.184 octeți; SHA-256 `b98827b4db68b606c36b2706480fce551ca944154235e64c265baa0f790edd06`.
- Imagine v7 intactă: SHA-256 `82a6f04eb8499182a4097c883880a24d72f8b0b365d04b55dc4c25d776096672`.
- Imagine originală intactă: SHA-256 `876a31e972a3c58ef29105306a0229ae4b8eaeb18de59a6aef8cf7bb66851a6b`.
- Patru verificări v8 au trecut. Arhiva ZIP de cod și raport verificată.

## Materiale generate
1. `DJ88-BID-K706-SELINUX-SI-AUDIT-v8.zip`: cod sursă C pentru audit/editarea xattr, test automat, README, raport JSON, APK extras din v8.
2. `DJ88-BID-K706-PRODUCT-SELINUX-v8.img`: imagine ext4 completă de analiză offline, cu BID inclus.

## Limite și reguli de siguranță
**NU este un firmware flashabil sau un OTA semnat.** Nu am rulat un `e2fsck` complet, nici Android/SELinux runtime și nici testul pe dispozitivul real. În plus, imaginea v8 nu rezolvă independent bootloop-ul existent. Nu se flash-uiește și nu se redenumește `update.zip`.

Următorul pas tehnic: validarea sistemului de fișiere cu un instrument de verificare complet și construirea unei metode legitime de instalare/recuperare care să respecte verificarea OEM și compatibilitatea exactă a hardware-ului.
