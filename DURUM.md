# DURUM — miaza finds (devir paketi, 06.11.2026)

Ana dal `main` = `origin/main` + 1 commit (D-048, push yapılmadı). 219 test geçiyor.

---

## 1. Bilinen hatalar ve çözülmemiş sorunlar

| # | Sorun | Etki | Not |
|---|---|---|---|
| 1 | **Aramada bölme kodu yok.** SPEC 6.1 „2.2“ gibi bölme koduyla arama istiyor; `produkte.suchtext_erneuern` fach kodunu eklemiyor. | Kütüphanede yere göre arama çalışmaz. | Yer değişince suchtext de yenilenmeli (dikkat: plan yeniden numaralanınca kodlar değişir). |
| 2 | **Drive dosya zamanları:** çalışma klasörü Drive'da; git zaman zaman içeriği aynı dosyaları „M“ gösterir (Drive yarım boyut bildiriyor). | Yanlış „değişiklik var“ görüntüsü. | Depo ayarları konuldu; yine olursa `git add <dosya>` (içerik aynıysa fark çıkmaz). |
| 3 | `STATUS.md` eski: „212 test“, „Dilim 2 … main'de“ satırı, Dilim 4 satırı başka oturumdan; < 40 satır kuralına sığmak için sıkıştırılmış. | Yanıltıcı. | Sıradaki ilk iş olarak düzeltilmeli. |
| 4 | `app/version.py` hâlâ `0.1.0`; kendi kuralına göre Dilim 1–3 bitince `0.3.x` olmalıydı. | Sürüm ekranda yanlış. | Karar gerektirmez, kurala uymak yeterli. |
| 5 | SPEC iç çelişkileri (DEVIR.md 4c): SPEC 10 „20'li etiket“, SPEC 11.3 açık görünüyor, SPEC 12 „oda renkleri yok“, 8.3/8.4 klasör yolları. | Yeni oturum yanlış yönlenebilir. | Bir belge commit'iyle düzeltilmeli (Cankat'a sorarak, karar değişikliği değil temizlik). |
| 6 | D-046 ve D-047 Almanca yazılmış; diğer kararlar Türkçe. | Tutarsızlık. | İsterse Türkçeye çevrilir (içerik değişmez). |
| 7 | Etiketten listesindeki Fach alt satırı hâlâ D-020 kuralıyla („Fach adı, yoksa ünite adı“); etiketin kendisi D-036/37 ağacını basıyor. | Küçük tutarsızlık. | Bilinçli bırakıldı (D-036: „listede alt satır aynı kalır“). |
| 8 | `openpyxl` bağımlılığı kurulu ama kullanılmıyor. | Gereksiz bağımlılık. | v2 Excel dışa aktarımı için; kaldırma kararı yok. |
| 9 | `demo/EKRANLAR.md` ve `demo/ekranlar/` git'e eklenmemiş. | Kaybolabilir (yalnız Drive'da). | Kim/ne zaman ekledi BİLİNMİYOR; eklenip eklenmeyeceğini Cankat'a sor. |
| 10 | `finds.db`'nin şema durumu BİLİNMİYOR (Migration 008–011 beta açılınca uygulanır). | — | Beta'yı yeni kodla bir kez açınca uygulanır; önce yedek önerilir. |

---

## 2. Açık sorular (Cankat'tan cevap bekleyenler)

1. **QR'ın kalıcı adresi ve HTTPS.** Hangi alan adı (ör. `finds.miaza.design`), DNS nerede yönetiliyor (Wix mi, World4You mu)? Cankat „sonra bilgi vereceğim“ dedi. Cevap gelince: `MF_BASIS_URL`, teknisyen belgesi ve SPEC 8.2 güncellenir. Toplu etiket basımından **önce** karar verilmeli.
2. **mkcert ile deneme HTTPS** ne zaman? (Ertelendi.) mkcert indirmek izin ister; telefona kök sertifikayı Cankat kurar.
3. **Mini PC ne zaman kurulacak?** Teknisyen belgesi hazır ama denenmedi.
4. **Gerçek dünya testi:** etiketleri basıp telefonla okutma ve geri bildirim listesi (02.11'den beri bekliyor).
5. **SPEC 11.4:** Google Drive masaüstü uygulaması mini PC'de olacak mı? (Yedeklerin Drive kopyası buna bağlı.)
6. **SPEC 11.5:** de-AT biçimleri ve Almanca terimlerin kesinleşmesi („Bibliothek“ bölüm adı ile doküman klasörü „Bibliothek“ çakışması dahil).
7. **SPEC 11.6:** finds ve counts vurgu renkleri (finds şu an amber).
8. **Docker yolu kaldırılsın mı?** D-003: kurulum yolu belli olunca kullanılmayan kaldırılır. Mini PC Windows ve `start.bat` ile kurulacak; Docker'ın kaldırılması henüz sorulmadı.
9. **Dokümanlar (dilim 4, sıradaki):** doküman kök klasörü nerede (sunucuda hangi yol)? SPEC 6.9 tek kök klasör istiyor; yolu BİLİNMİYOR.
10. **Gece yedeği:** Windows'ta zamanlayıcı mı (Görev Zamanlayıcı), uygulamanın içinde mi? Drive kopyası klasörü? Karar yok.

---

## 3. Yapılan testler

### 3a. Otomatik (pytest, 219 test, hepsi geçiyor, 06.11.2026, ~45 sn)
Komut: `%USERPROFILE%\miaza-local\finds\.venv\Scripts\python -m pytest -q`. Her test geçici bir veritabanı kullanır (`conftest.py`).

| Dosya | Test | Kapsam |
|---|---|---|
| test_grundgeruest | 10 | Başlangıç, güvenlik başlıkları, 404, köken (Origin) kontrolü, migration koruması |
| test_bibliothek | 11 | Arama, filtreler, durum, sayaçlar |
| test_produkte | 17 | Ürün CRUD, fiyat, renk, sürüm kontrolü, kategori değişimi |
| test_serie | 4 | Seri kayıt |
| test_sammel | 8 | Toplu düzenleme + geri al |
| test_kategorien | 13 | Kategori/filtre kuralları |
| test_farben | 5 | Ana renk/ton, Migration 006 |
| test_plan | 18 | Plan, ünite, fach, yer, yeniden numaralama |
| test_etiketten | 16 | PDF düzeni, kenar boşlukları (piksel ölçümü), rulo, fach etiketi, satır kaydırma |
| test_system | 15 | Systembereich: kurulum, giriş, kilitlenme, şifre/anahtar, yedek, geri yükleme, taşıma, seçerek silme |
| test_personen | 4 | Kişiler, Migration 008 |
| test_entnahme | 9 | Al/koy, geri alma, durum filtresi, bölme onayı, yeni yer, einordnen, ayar, Migration 009 |
| test_bearbeitung | 4 | „Wird bearbeitet“: iki cihaz, sona erme (sahte saat), hatalı giriş |
| test_sammlungen | 7 | Koleksiyonlar, Migration 011 |
| test_seiten | 9 | Sayfalar yükleniyor, menü, metin anahtarları, Scannen sayfası |
| test_stil | 5 | CSS sınıfları tanımlı, yalnız yazı basamakları, renkler yalnız token, koyu tema tam, her ikon var |
| test_migration_001/003/004/005 | 12/4/1/1 | Şema |

### 3b. Elle, tarayıcıda (Claude'un tarayıcı paneli, dev sunucusu, dev.db)
- **Etiketler:** PDF/PNG çizilip kenarlar piksel ölçümüyle doğrulandı; rulo PDF 17 sayfa 70×38; Fach etiketi örnekleri (kısa/uzun/tek ad) gözle.
- **Kişiler:** ekleme, cihaz kişisi seçme, ad değiştirme, kaldırma + geri al (telefon boyutunda).
- **Al/koy:** telefon ve masaüstü panelde Nehmen formu, Außer Haus + not, Zurücklegen, iki yönde geri al, filtre ve rozet.
- **Scannen:** kamera paneli kamerayı engellediği için yalnız **foto yolu** denendi; foto, gerçek bir etiket resmi DataTransfer ile verilerek simüle edildi. Ürün/fach QR'ı, tanınmayan kod, kod kutusu.
- **Bölme onayı:** doğru bölme, yanlış bölme → yeni yer → geri al (eski yer döndü), ürün etiketi okutma, ayar Aus.
- **Einordnen:** konumsuz ürün, başka bölmedeki ürün (soru), başka fach etiketi (hedef sorusu), satır geri al, Fertig.
- **Wird bearbeitet:** ikinci cihaz fetch ile taklit edildi; ürün formu, plan, kategori; serbest kalınca şerit; sayfadan çıkınca işaretin kalkması.
- **D-045:** Büro'da raf önce (telefon boyutu), çoklu foto kırpma „1 / 2“, varsayılan Rolle.
- **Gerçek sistem (8090):** Verano aktarımı API ile; etiket PNG'si gerçek veriden çizilip bakıldı (salt okuma).

### 3c. Hiç test edilmemiş
- **Gerçek telefonda** hiçbir Dilim 3 akışı: canlı kamera (HTTPS yok), telefonun kamera uygulamasıyla foto, titreşim, `sendBeacon` ile işaret bırakma.
- **Canlı kamerayla art arda okutma** (Scannen, bölme onayı, einordnen'de canlı mod) — kod var, hiç çalıştırılmadı.
- **İki gerçek cihazla** aynı anda düzenleme.
- **Gerçek QL-570'e uygulamanın PDF'inin basılması** (Cankat'ın kendi PDF ile denemesi çalıştı; bizim rulo PDF'imiz basılmadı).
- **Etiketin telefonla okunması** (basılı QR → ürün sayfası).
- **Docker** yolu (Dockerfile, compose) hiç çalıştırılmadı.
- **Mini PC kurulumu ve teknisyen belgesi**; Görev Zamanlayıcıyla otomatik başlatma; `MF_BASIS_URL` ile QR.
- **Gerçek ofis planıyla uzun çizim** (plan düzenleyici).
- **Systembereich'te gerçek yedek/geri yükleme** beta verisiyle (testlerde var, gerçek veride değil).
- **İstatistik ve Koleksiyonlar** bu oturumda tarayıcıda görülmedi (başka oturum yaptı; testleri geçiyor).
- **Performans** (SPEC: arama < 200 ms, birkaç bin ürün) ölçülmedi.

---

## 4. Teknik borç ve kırılgan noktalar

1. **Çalışma klasörü Google Drive'da.** Git klasörü taşındı ama kod dosyaları hâlâ Drive'da: dosya zamanları, yarım boyutlar, `desktop.ini` dosyaları. Paralel oturumlar (aynı klasörde) birbirinin değişikliğini görmeden çalışabilir.
2. **„Wird bearbeitet“ işareti sunucu belleğinde**: tek süreç varsayımı (uvicorn tek worker). Birden çok worker ya da yeniden başlatma işaretleri sıfırlar (bilinçli, SPEC 7: kalıcı değil).
3. **Basılı etiketler QR adresine bağlı.** Kalıcı adres kararlaştırılmadan basılan etiketler adres değişince telefon kamerasıyla açılmaz (uygulama içi tarayıcı adresi yok sayar, D-040).
4. **HTTPS yok** → canlı kamera yok; telefonda okutma foto yoluyla yavaş. Bölme onayı ve toplu yerleştirme pratikte HTTPS'e bağlı.
5. **Dev sunucusu `--reload`suz**; her değişiklikten sonra elle yeniden başlatma unutulursa eski kod test edilir.
6. **`texte.py` tek büyük sözlük**; anahtar testleri var (`test_alle_verwendeten_textschluessel_gibt_es`).
7. **Etiket ölçüleri pt/mm sabitleri** (`etiketten.py`: RAND, QR_SEITE, MARKE_PT, ORT_*): kâğıt değişirse JSON yetmeyebilir, düzen sabitleri de gözden geçirilmeli.
8. **jsQR dosyası elle eklendi** (npm 1.4.0); güncelleme süreci yok.
9. **Python sürümleri farklı:** venv 3.14.5, Dockerfile 3.13, SPEC „3.12+“.
10. **Bash ortamında `gh` ve `node` yok**; GitHub işleri ve JS sözdizimi denetimi tarayıcı/elle.
11. **Yolu çok uzun Drive klasörü**: Windows 260 karakter sınırı; geçici dosyalar kısa yola yazılmalı.

---

## 5. Sıradaki 3 adım

1. **Belgeleri temizle (küçük, karar gerektirmez):** STATUS.md'yi gerçek duruma getir (219 test, Dilim 4 durumu), `version.py`'yi kurala göre artır (Cankat'a sorarak), SPEC'teki dört çelişkiyi (10 „20'li“, 11.3, 12 oda renkleri, 8.3/8.4 yolları) düzelt; D-048 commit'ini Cankat isterse push et.
2. **Dilim 4 / Dokumente (SPEC 6.9, D-004):** önce kök klasör yolunu ve kapsamı Cankat'la netleştir, D-numarası yaz, sonra kod (kök klasör ayarı, göreli yol, aç, „bulunamadı“).
3. **Dilim 4 / Gece yedeği (SPEC 8.4):** zamanlayıcının yeri (Windows Görev Zamanlayıcı mı, uygulama içi mi) ve Drive kopyası için karar; ayarlarda son yedek zamanı ve 2 gün uyarısı.

Paralelde Cankat'tan beklenenler: alan adı/HTTPS bilgisi, gerçek dünya testi geri bildirimi, mini PC kurulum zamanı.
