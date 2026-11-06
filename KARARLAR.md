# KARARLAR — miaza finds (devir paketi, 06.11.2026)

İki bölüm:
- **A. Dosyalarda yazmayan kararlar ve anlaşmalar.** Yalnız bu sohbette konuşuldu; başka yerde yok. En değerli kısım.
- **B. Kayıtlı kararların dizini** (D-001…D-048, `DECISIONS.md`). Her biri bir satırda; ayrıntı DECISIONS.md'de.

Kaynak notu: bu sohbetin 02.11.2026 öncesindeki kısmını (Dilim 1, D-001…D-017) ben doğrudan görmedim. O dönemin kararlarını
yalnız DECISIONS.md'den aktarıyorum. 02.11–06.11 arası kısmı bir özet ve sohbetin kendisinden biliyorum. Emin olmadığım
yerlerde „BİLİNMİYOR“ ya da „tahmin“ yazdım.

---

## A. Dosyalarda yazmayan kararlar ve anlaşmalar

### A1. Çalışma ve güvenlik kuralları

| # | Karar / anlaşma | Gerekçe | Ne zaman |
|---|---|---|---|
| A1.1 | **Beta sunucusuna (8090) ve `finds.db`'ye Claude kendiliğinden dokunmaz.** Beta'yı Cankat `start.bat` ile açar ve kapatır; Claude onun sürecini kapatmaz. Gerçek veriye yazmak yalnız Cankat açıkça isteyince olur (örnek: Verano aktarımı, A3.2). | Gerçek veri Cankat'ın. Deneme `dev.db` (8091) üzerinde yapılır. | 02.11.2026'dan beri |
| A1.2 | **Şifre girilmez.** Systembereich'in yönetici hesabını Cankat kurar ve kullanır; Claude orada oturum açmaz. | Güvenlik kuralı. | 02.11.2026'dan beri |
| A1.3 | **main'e birleştirme yalnız Cankat onaylayınca.** Dilim dalda geliştirilir; birleştirme sorulur. | Cankat'ın isteği. Dilim 2 ve 3 onayla birleştirildi (04.11). | 02.11–04.11 |
| A1.4 | **Push yalnız istenince.** (CLAUDE.md'de de var.) Uzak depo kurulunca da geçerli. İkinci bir push'u Claude Code'un otomatik izin denetimi durdurdu, çünkü Cankat o anda istememişti. | Cankat'ın kuralı. | Süregelen; 04.11'de teyit |
| A1.5 | **Kendi önerini işaretle ve onay iste.** Her DECISIONS girişinde „Claude'un ekledikleri (onay bekliyor)“ satırı; Cankat toplu karara bağlar. | CLAUDE.md kuralı; D-045'te bekleyenlerin hepsi karara bağlandı. | Süregelen |
| A1.6 | Dosya indirme (ör. jsQR) **önce sorulur**; kaynak, ad, boyut söylenir. | Güvenlik kuralı. jsQR 1.4.0 onaylandı (D-040). | 04.11.2026 |
| A1.7 | Dev sunucu **her kod değişikliğinden sonra yeniden başlatılır.** Değişiklik tarayıcıda görülmeden „bitti“ denmez. | `--reload` yok; asset karması başlangıçta hesaplanıyor. Cankat bir kez eski hâli gördü (02.11, etiket). | 02.11.2026 |

### A2. Altyapı ve depo

| # | Karar | Gerekçe | Ne zaman |
|---|---|---|---|
| A2.1 | **Özel GitHub deposu:** https://github.com/cankatdonmez/miaza-finds (`origin`). Yalnız `main` yüklendi; dilim dalları main'e birleşmiş olduğu için yüklenmedi. | Kodun yedeği. Cankat önerdi, depoyu kendisi açtı (Bash'te `gh` yok). | 04.11.2026 |
| A2.2 | (06.11'de A8.1 ile aşıldı) **Git klasörü Drive dışına taşındı:** `C:\Users\canka\miaza-local\finds\git`. Drive'daki `.git` artık `gitdir:` satırı olan bir dosya. Depo ayarları: `core.trustctime=false`, `core.checkStat=minimal`. | Drive, git'in `index.lock` dosyasını silinse de geri getiriyordu, birleştirme durdu. Dosya boyutlarını da yarım bildirdi. Cankat onayladı. | 04.11.2026 |
| A2.3 | Başka bir bilgisayarda çalışmak için depo **GitHub'dan indirilir**. Drive'daki klasörde git yalnız bu bilgisayarda çalışır. | A2.2'nin sonucu. | 04.11.2026 |
| A2.4 | `wt-sammlungen` çalışma kopyası ve `sammlungen` dalı **kalsın** (temizlenmesin). | Cankat'ın isteği. Dal main'e birleşmiş, içinde değişiklik yok. | 06.11.2026 |
| A2.5 | Ege Seramik sitesinden indirme Python'un varsayılan sertifika deposuyla başarısız oldu („certificate has expired“). Çözüm: `httpx` (güncel sertifika listesi). **Sertifika doğrulaması kapatılmadı.** | Güvenlik. | 02.11.2026 |

### A3. Veri

| # | Karar | Gerekçe | Ne zaman |
|---|---|---|---|
| A3.1 | **Verano (Ege Seramik) serisi dev.db'ye eklendi:** 17 ürün, FL-009 … FL-025 (envanter 12–28), 39 fotoğraf. Marka „Ege Seramik“, Artikelnummer = Ege ürün kodu (ör. 100X300VRO46), ölçü „10 × 30 cm, 9 mm“, link = ürün sayfası, Almanca not, „Farbton“ = en yakın ana renk. Aktarma betiği (`verano_import.py`) Claude'un geçici klasöründeydi; hâlâ duruyor mu BİLİNMİYOR, projede yok. | Cankat'ın gerçek dünya testi için örnek veri. | 02.11.2026 |
| A3.2 | **Aynı 17 ürün gerçek sisteme (`finds.db`, 8090) aktarıldı:** FL-005 … FL-021 (envanter 5–21). Gerçek sistemde Fliese'nin filtreleri farklı olduğu için: Breite 10, Länge 30, Dicke 9, Rutschhemmung = „Keine“, Bereich = „Wand“, Rektifiziert boş; ana renk `farben` alanına; Abmessungen boş bırakıldı. Fotoğraflar `C:\Users\canka\miaza-local\finds\import\verano`. | Cankat'ın açık isteği („Evet, aktar“). | 02.11.2026 |
| A3.3 | Ürün adları **üreticinin sitesindeki orijinal adlarıyla** girilir, çevrilmez. Verano adları Türkçe kalır (Türkçe sayfadan geldiği için). | Cankat (D-045'e de yazıldı). | 04.11.2026 |
| A3.4 | Renk eşlemesi: tonu ana renge bağla (Antrasit → Schwarz, Taupe/Kemik/Krem → Beige, Bronz/Kestane/Tarçın → Braun …). Cankat „doğru“ dedi. | D-031 mantığı. | 04.11.2026 |
| A3.5 | dev.db'de deneme kişileri: Cankat, Murat Y., Selin; bu tarayıcının kişisi Cankat. Deneme hareketleri: bazı Verano ürünleri alınmış/yerleştirilmiş durumda. | Deneme. | 04.11.2026 |
| A3.6 | `finds.db`'ye Migration 008–011'in uygulanıp uygulanmadığı **BİLİNMİYOR**: beta en son ne zaman yeni kodla başlatıldı, bilmiyorum. Migration'lar sunucu açılırken kendiliğinden uygulanır. | — | — |

### A4. Etiketler (DECISIONS'ta olmayan ayrıntılar)

| # | Karar | Gerekçe | Ne zaman |
|---|---|---|---|
| A4.1 | Etiket QR'ı **28 mm'den 26 mm'ye** küçültüldü: büyüyen „miaza“ ve geniş metin sütununa yer. Claude'un kararı, Cankat'a söylendi, itiraz gelmedi (açıkça onaylanmadı da). | D-034 düzeltmesi. | 02.11.2026 |
| A4.2 | „Ortala“ = sabit ızgara; metin sütunu içeriğe göre daralmaz. Cankat'ın düzeltmesi. | İlk deneme içeriğe göre kayıyordu. | 02.11.2026 |
| A4.3 | Uzun özellik satırı („10 CM \| 30 CM \| …“) kesilmez; „ \| “ işaretlerinde bölünüp boş satıra geçer, en fazla 4 satır, sonra „…“. Cankat onayladı. | „KEI…“ diye kesiliyordu. | 02.11.2026 |
| A4.4 | Rulo baskısı: **her etiket ayrı PDF sayfası**; P-touch Editor'ün veri içe aktarması kullanılmaz (düzen iki yerde tutulmasın). Sürücü ayarı: 38 mm sürekli, 70 mm uzunluk, her etiketten sonra kes, „Gerçek boyut“. | D-035'te var; sürücü ayarı yalnız sohbette ve teknisyen belgesinde. | 04.11.2026 |
| A4.5 | Fach etiketinde ağaç **kademeli**: ünite odanın, bölme ünitenin bir kademe altında, her biri kendi „└“ çizgisiyle (Cankat'ın düzeltmesi; ilk hâlde tek dikey çizgi vardı). | D-037'ye işlendi. | 04.11.2026 |
| A4.6 | Gerçek dünya testi (etiketi bas, telefonla okut) **Cankat yapacak**; geri bildirim tek liste. Henüz gelmedi. | — | 02.11'den beri açık |

### A5. Sunucu, ağ, HTTPS

| # | Karar | Gerekçe | Ne zaman |
|---|---|---|---|
| A5.1 | **Mini PC Windows** olacak, henüz kurulmadı. Kurulumu bir teknisyen yapacak. Almanca teknisyen belgesi: https://claude.ai/artifact/KtCQDEkSQeHfcE4NGtbAoW (DHCP rezervasyonu, Windows ayarları, `C:\miaza\finds`, `MF_BASIS_URL` setx, güvenlik duvarı, Görev Zamanlayıcı ile `start.bat netz`, QL-570, yedek, kabul listesi). Almanca, çünkü teknisyen Viyana'da varsayıldı. **Hiç denenmedi.** | Cankat'ın isteği. | 04.11.2026 |
| A5.2 | (A8.4/A8.5: bekletiliyor) **QR'ın kalıcı adresi ve HTTPS açık; Cankat bilgi verecek.** Claude'un önerisi: şimdiden bir alt alan adı (ör. `finds.miaza.design`) `MF_BASIS_URL` olsun; DNS Wix'te ya da World4You'da kalabilir; Let's Encrypt sertifikası „DNS alias mode“ ile. World4You'da büronun bir hosting paketi var; hosting'in kendisi gerekmiyor, DNS'i işe yarar. Bu konuda teknisyen belgesi sonra güncellenecek. | Basılı etiketler adrese bağlı; HTTPS canlı kamera için gerekli. | 04.11.2026 |
| A5.3 | World4You'nun resmî DNS API'si bulunamadı; acme.sh'in `dns_world4you` eklentisi hesap şifresiyle çalışıyor gibi (bir özetten okundu, doğrulanmadı). Bu yüzden alias yolu önerildi. | — | 04.11.2026 |
| A5.4 | **mkcert ile deneme amaçlı HTTPS** (canlı taramayı gerçek telefonda görmek için) **sonraya bırakıldı** (Cankat: „sonra yaparız denemek için“). mkcert'i indirmek ayrıca izin ister; kök sertifikayı telefona Cankat kurar. | — | 04.11.2026 |
| A5.5 | Tek ürün için telefonun kendi kamerası yeterli (etiketteki QR bir link). Uygulama içi taramanın asıl değeri art arda okutmada; bu da HTTPS ile rahatlar. | Cankat'ın „foto aufnehmen gereksiz adım“ eleştirisinden. | 04.11.2026 |

### A6. Kapsam ve sıra

| # | Karar | Gerekçe | Ne zaman |
|---|---|---|---|
| A6.1 | Kart yayı / yelpaze animasyonları **Dilim 3'ten sonra**, gerçek veriyle „Tekrar bak“ adımında. | D-017 + D-038. Hâlâ yapılmadı. | 04.11.2026 |
| A6.2 | **Linkten doldurma en son** eklenecek özelliklerden; yol yapay zekâ destekli okuma (Claude API). Cankat'ın gerekçesi: onlarca firma, farklı malzeme türleri, farklı diller; API'siz olmaz. | D-048'e yazıldı. | 06.11.2026 |
| A6.3 | Dilim 4 sırası: Statistik → Sammlungen → Dokumente → Nachtsicherung → Almanca son okuma. Bu kararı başka bir oturum yazdı (D-046), „Cankat seçti“ diyor; ben o konuşmayı görmedim. | — | 04.11.2026 |
| A6.4 | 04.11 akşamı (21:47–22:32) Dilim 4'ün ilk iki adımını yapan oturum, **büyük ihtimalle Cankat'ın terminalde açtığı Claude Code oturumu** (tahmin; uygulamanın oturum listesinde görünmüyor). D-046 ve D-047'yi Almanca yazmış. | — | 06.11.2026'da fark edildi |
| A6.5 | „İyi tasarımın ilkeleri“ denetiminde ilk denetim yüzeysel bulundu (Cankat: „sadece bunları mı buldun?“); kontrol listesine göre yeniden yapıldı → D-029/D-030. | Denetim, kontrol listesine madde madde bakılarak yapılır. | 02.11.2026 |

### A8. Devir paketinden sonra (D-049, 06.11.2026)

| # | Karar | Gerekçe |
|---|---|---|
| A8.1 | **Google Drive tamamen aradan çıktı.** Çalışma kopyası `C:\Users\canka\Documents\miaza-finds` (yerel git deposundan klon, `origin` GitHub). Eski Drive klasörü ve eski git deposu (`miaza-local\finds\git`) yedek olarak duruyor; silme kararı Cankat'ın. | Cankat: „karışıklık çıkarıyorsa Drive'ı tamamen aradan çıkarabilirsin; zaten GitHub'dan devam ediyoruz.“ |
| A8.2 | **Etiket biçimleri yalnız iki:** A4 24'lü (3×8) ve 38 mm Brother rulo. 20'li ve 40'lı düzenlerle iş yok; SPEC'ten kalıntılar silindi. | Cankat. |
| A8.3 | **Otomatik (gece) yedek bekletiliyor;** uygulama belli bir noktaya gelince konuşulacak. | Cankat: „şu an acelesi yok.“ |
| A8.4 | **HTTPS bekletiliyor.** | Cankat: „şu an bir şey yapamayız.“ |
| A8.5 | **Bütün mevcut veri ve QR'lar demo.** Gerçek veri ve kalıcı QR'lar uygulama tamamlanıp sunucuya kurulunca; QR adresi için dikkat edilecekler o aşamada konuşulacak. | Cankat. |
| A8.6 | Eski kalıntılar SPEC'ten temizlendi (20'li etiket, kapanmış soru 11.3, „oda renkleri yok“, `DATA/Apps` yolları); `version.py` 0.3.0; STATUS güncel. | Cankat: „eskiden kalmış olanları kaldırmak gerekli.“ |

### A7. Düzeltilen hatalar (karar sayılmaz ama bilinmeli)

- Plan'da ünitelere tıklanamıyordu: `setPointerCapture` tıklamayı svg'ye yönlendiriyordu → 4 px hareketten sonra yakalanıyor.
- Telefonda kamerayla çekilen foto ne kırpılıyor ne ekleniyordu: iki kez çözümleme + boş dosya tipi → tek `<img>` çözümleme, boş tip kabul.
- Mehrfarbig tonu gri görünüyordu → kendi işareti.
- Etiket önizleme resimleri aynı anda istenince pdfium hata veriyordu → kilit (`_PDFIUM`).
- `check` simgesi hiç tanımlanmamıştı (seçim işaretleri görünmüyordu) → eklendi, test (`test_jedes_benutzte_symbol_gibt_es`).
- Kişi eklerken hızlı yazınca ikinci ad kayboluyordu → alan hemen boşaltılıyor.
- Olmayan ürün numarası Scannen'de boş sayfa açıyordu → „nicht erkannt“.

---

## B. Kayıtlı kararların dizini (DECISIONS.md)

Tarih biçimi gg.aa.yyyy. „C“ = Cankat'ın kararı/isteği, „Cl“ = Claude'un önerisi (onaylı).

| No | Tarih | Karar (bir satır) | Kimden / gerekçe |
|---|---|---|---|
| D-001 | 01.11 | Port çiftleri: counts 8080/8081, finds 8090/8091, sonrakiler 8100/8101… | C: aynı mini PC'de çakışma olmasın |
| D-002 | 01.11 | Yazı sistemi counts'tan: Figtree + IBM Plex Mono, `--fs-*` ölçeği | C |
| D-003 | 01.11 | Docker ve start.bat birlikte; kurulumdan sonra kullanılmayan kaldırılır | Mini PC işletim sistemi belli değildi |
| D-004 | 01.11 | Dokümanlar dilim 4'te | Kapsam |
| D-005 | 01.11 | Belge düzeni counts gibi | Aile tutarlılığı |
| D-006 | 01.11 | Systembereich: tek yönetici + şifre; yedek, silme, veri değiştirme | C |
| D-007 | 01.11 | Origin kontrolü; Systembereich'te oturum + CSRF | Cl, teknik |
| D-008 | 01.11 | `.venv`, veritabanları, media Drive dışında (`miaza-local\finds`) | Drive senkronu bozuyor |
| D-009 | 01.11 | Veri taşıma: tek dosya dışa aktar / içe al | C |
| D-010 | 01.11 | Güvenlik anahtarıyla şifre sıfırlama | C |
| D-011 | 01.11 | Ürün içeren kategori silinmez | C |
| D-012 | 01.11 | Toplu düzenleme (masaüstü liste görünümü) | C, kanıtla |
| D-013 | 02.11 | „Alles löschen“ numaraları 1'den başlatır (sonra D-025 ile değişti) | Cl |
| D-014 | 02.11 | Beta geri bildirimi 1: masaüstü kamera, Option „+“, QR ağ adresi | C'nin denemesi |
| D-015 | 02.11 | Görsel boyutları ekrana göre (320/960/2400) | Cl |
| D-016 | 02.11 | „Hier einordnen“ 30 dk modu (uygulama içi tarayıcısız) | Cl |
| D-017 | 02.11 | Dilim 2 kapsamı; kart yayı/yelpaze sonra | Cl |
| D-018 | 02.11 | Plan yazıları şeklin içinde, okunur boyda (renk kısmı D-024 ile değişti) | C'nin geri bildirimi |
| D-019 | 02.11 | Dikdörtgen ünite duvara/komşuya yapışır, çarpışmaz; Alt serbest | C |
| D-020 | 02.11 | Bölmenin isteğe bağlı adı (Migration 004) | C |
| D-021 | 02.11 | Ürün detayında „Platz ändern“ (seçici D-022 ile kalktı) | C |
| D-022 | 02.11 | Yer Büro'da seçilir: plan → ünite → bölme → „Hier ablegen“ | C'nin düzeltmesi: ayrı pencere değil |
| D-023 | 02.11 | Tema: beyaz / antrasit, amber vurgu; Außer Haus gül; `THEMA.md` | C (değerler Cl) |
| D-024 | 02.11 | Oda rengi 6 pastelden seçilir; üniteler odanın tonunda (Migration 005) | C |
| D-025 | 02.11 | Systembereich'te seçerek silme (onay kutuları) | C |
| D-026 | 02.11 | Ünite fotoğrafında bölmeler demodaki gibi (etiket, spot, nabız) | C |
| D-027 | 02.11 | Foto eklerken kırpma (çoklu seçim kısmı D-045 ile değişti) | C |
| D-028 | 02.11 | Düzenlemede her şey „Speichern“e kadar taslak; seri sonrası „Speichern“ çubuğu | C'nin denemesi |
| D-029 | 02.11 | Tasarım denetimi önem 2: kısa form, 44 px, onay penceresi yok, tek ad „Verwerfen“ | Cl, onaylı |
| D-030 | 02.11 | Tasarım denetimi önem 1: açıklama metni kalkar, çizim yalnız masaüstü | Cl, onaylı |
| D-031 | 02.11 | 14 ana renk + kategoriye özel „Farbton“ (Farbkasten), Migration 006 | C (2. yöntem) |
| D-032 | 02.11 | Yeni renk filtresi ana renk tonlarıyla dolu başlar | C |
| D-033 | 02.11 | Etiket kâğıdı A4 3×8, ürün etiketi düzeni, Artikelnummer (Migration 007) | C'nin PDF'i |
| D-034 | 02.11 | Etiket: 3 mm güvenli alan, sabit ızgara, QR solda dikey ortalı, „miaza“ Comfortaa | C |
| D-035 | 04.11 | Rulo etiket 70×38 (QL-570, DK-22225), sayfa başına bir etiket | C |
| D-036 | 04.11 | Fach etiketinde oda / ünite / bölme alt alta | C |
| D-037 | 04.11 | Fach etiketi: kademeli ağaç, alanı dolduran yazı, „…“ son çare | C'nin düzeltmesi |
| D-038 | 04.11 | Dilim 3 kapsamı ve sırası (6 parça) | Cl, onaylı |
| D-039 | 04.11 | Nehmen / Zurücklegen, durum çıkış kaydından (Migration 009), detayda başlık altında | Cl |
| D-040 | 04.11 | Scannen sayfası, jsQR, QR adresinin yalnız sonu okunur | Cl, jsQR C onayı |
| D-041 | 04.11 | HTTPS yokken Scannen kamerayı doğrudan açar, foto sonrası geri bildirim | C'nin eleştirisi |
| D-042 | 04.11 | Fach bestätigen; büro ayarı Ein/Aus (Migration 010) | Cl |
| D-043 | 04.11 | Okutarak toplu yerleştirme (`/scannen?fach=`) | Cl |
| D-044 | 04.11 | „Wird bearbeitet“: bellekte işaret, 30 sn sinyal, 2 dk / 15 dk sona erme | Cl |
| D-045 | 04.11 | Bekleyen önerilere C'nin kararları: raf önce, her foto kırpılır, varsayılan Rolle, tanınmayan kodda soru, hedef değişiminde soru, orijinal adlar | C |
| D-046 | 04.11 | Dilim 4 İstatistik ile başlar; telefonda „Mehr“ (başka oturum, Almanca) | C (o oturuma göre) |
| D-047 | 04.11 | Sammlungen miktarsız, Migration 011 (başka oturum, Almanca) | Cl, C „ayrıntı vermedi“ |
| D-048 | 06.11 | Linkten doldurma: yapay zekâ destekli okuma, en son | C |
| D-049 | 06.11 | Yalnız A4 24'lü + 38 mm rulo; SPEC kalıntıları silindi; Windows klasör düzeni; Drive aradan çıktı; yedek, HTTPS, gerçek QR bekletiliyor | C |
