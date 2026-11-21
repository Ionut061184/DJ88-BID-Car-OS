# DJ 88 BID — v15: verificare criptografică reală a OTA original (21.11.2026)

## Rezultat real
- Firmware original `update.zip`: **2.433.335.709 octeți**.
- SHA-256: `bed3277a4553ed2993e11636c5b625557dfd2d72d1da00dd6c3c7d2ad250614e`.
- CRC pentru toate intrările ZIP: **PASS**.
- Semnătură ZIP recovery whole-file PKCS7: **PASS**, verificată cu OpenSSL CMS pe cei **2.433.334.129 octeți** semnați, nu doar prin existența certificatului.
- Certificatul semnatar: `qianfeng@qianfeng.com`, subject `CN=liuhualiang,OU=Research,O=QF,L=ShenZhen View,ST=GuangDong,C=CN`.
- Certificat OTA cu amprentă SHA-256 `8b0e3806971194623315f80db1b201f8b9ad0d518ff3c8565f45931b433b3bb5`; coincide cu semnatarul PKCS7.
- `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img`: magic `AVB0` prezent. **Nu** înseamnă că semnăturile AVB au fost verificate criptografic.
- **6 teste automate** au trecut pentru validarea structurii footerului ZIP.
- Firmware original și imaginile ext4 v7/v8 nemodificate.

## Blocaj important confirmat
Orice înlocuire a `product.new.dat.br` cu o imagine modificată ar invalida semnătura OTA whole-file QF. APK-ul BID folosește altă cheie decât semnătura firmware-ului. Fără cheia OTA privată OEM, sau o cale de instalare autorizată care acceptă alt certificat, nu există un update modificat sigur de prezentat drept instalabil.

Validarea `openssl cms -verify -noverify` verifică semnătura criptografică pe conținut, nu verifică lanțul de încredere al certificatului. Certificatul semnatar a fost comparat separat cu cel inclus în OTA.

## Livrabil
`DJ88-BID-K706-VERIFICARE-SEMNATURA-OTA-v15.zip`: `verify_k706_ota.py` (citire, CRC, certificat, verificare CMS streaming), `test_verify_k706_ota.py` (6 teste), raport JSON real și README.

**Nu este un firmware flashabil.** Nu repară de unul singur bootloop-ul. Verificarea completă `e2fsck` a copiei PRODUCT și compatibilitatea exactă K706/MCU/display rămân neconfirmate. Nu se încearcă KEY2/flash în absența validării.


## Compatibilitate: limită verificată din metadata OTA
Fișierul `META-INF/com/android/metadata` al originalului semnat declară:
- `post-build=ROCO/K706/K706:10/QP1A.190711.020/55446:user/release-keys`
- `post-sdk-level=29`, `post-security-patch-level=2020-06-05`
- `post-build-incremental=55446`, `pre-device=K706`.

Versiunea software fotografiată pe aparatul fizic este `QF001.20250530.200511`, însă OTA nu declară direct această versiune de UI. Prin urmare, verificarea criptografică și potrivirea numelui K706 **nu certifică** compatibilitatea cu configurația existentă.

Scriptul OTA verifică `ro.qf.platform=7862` și apoi scrie direct uboot, vbmeta, boot și recreează dynamic partitions; nu include o verificare explicită în script a variantei de ecran 1280 × 720, a MCU QF05 sau a DSP BU32107. **Nu se recomandă flash pe dispozitiv.**
